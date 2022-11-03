import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.core.management import BaseCommand
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from main.models import Tag
from main.models.user import User
from main.serializers.user_serializer import CNFS_RESERVED_TAG_NAME
from moine_back.settings import BASE_DIR, DOMAIN, IS_LOCAL_DEV

from csv import DictReader

source_file_path = BASE_DIR / "cnfs_accounts.csv"
UserModel = get_user_model()


class MyPasswordResetForm(PasswordResetForm):
    """Same form, but we add the possibility to send to multiple emails."""

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Exact copy-paste of PasswordResetForm.send_mail, but to_email is a list
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        # below line is only change
        email_message = EmailMultiAlternatives(subject, body, from_email, to_email)
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, "text/html")

        email_message.send()

    def save(
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.html",
        use_https=False,
        token_generator=default_token_generator,
        from_email=None,
        request=None,
        html_email_template_name=None,
        extra_email_context=None,
        extra_email=None,
    ):
        """
        Exact copy-paste of PasswordResetForm.save, but we've added `extra_email` arg
        """
        email = self.cleaned_data["email"]
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override
        email_field_name = UserModel.get_email_field_name()
        for user in self.get_users(email):
            user_email = getattr(user, email_field_name)
            context = {
                "email": user_email,
                "domain": domain,
                "site_name": site_name,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": token_generator.make_token(user),
                "protocol": "https" if use_https else "http",
                **(extra_email_context or {}),
            }
            to_mail = [user_email]
            if extra_email:
                to_mail.append(extra_email)
            self.send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                to_mail,
                html_email_template_name=html_email_template_name,
            )


def import_accounts(limit_to_emails=None, max_n_accounts=None):
    with open(source_file_path) as fh:
        reader = DictReader(fh, delimiter=";")

        try:
            cnfs_tag = Tag.objects.get(name=CNFS_RESERVED_TAG_NAME)
        except Tag.DoesNotExist:
            cnfs_tag = None

        n_accounts_created = 0
        for line in reader:
            if max_n_accounts and n_accounts_created >= max_n_accounts:
                print(f"already created {max_n_accounts} accounts")
                break

            email = line["Email @conseiller-numerique.fr"]
            private_email = line["Email"]
            if not email:
                continue

            if (
                limit_to_emails
                and email not in limit_to_emails
                and private_email not in limit_to_emails
            ):
                continue

            # check if user already exists
            cnfs_id = line["Id du conseiller"]
            if (
                User.objects.filter(email=email).exists()
                or User.objects.filter(cnfs_id=cnfs_id).exists()
            ):
                print(f"compte déjà créé pour cet {email} - {cnfs_id}")
                continue

            # create account
            user_data = dict(
                email=line["Email @conseiller-numerique.fr"],
                password=str(uuid.uuid4()),
                first_name=line["Prénom"],
                last_name=line["Nom"],
                cnfs_id=cnfs_id,
                is_active=True,
            )
            n_accounts_created += 1
            user = User.objects.create_user(**user_data)
            if cnfs_tag:
                user.tags.add(cnfs_tag)

            # send custom password forgotten email
            form = MyPasswordResetForm(dict(email=email))
            if form.is_valid():
                form.save(
                    email_template_name="email/cnfs/cnfs_account_creation_email.html",
                    subject_template_name="email/cnfs/cnfs_account_creation_subject.txt",
                    domain_override=DOMAIN,
                    extra_email_context={
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    extra_email=private_email,
                    use_https=not IS_LOCAL_DEV,
                )

            print(f"utilisateur {email} - {private_email} ajouté")


def import_cnfs_organizations(limit_to_emails=None, max_n_accounts=None):
    with open(source_file_path) as fh:
        reader = DictReader(fh, delimiter=";")

        try:
            cnfs_tag = Tag.objects.get(name=CNFS_RESERVED_TAG_NAME)
        except Tag.DoesNotExist:
            cnfs_tag = None

        n_accounts_created = 0
        for line in reader:
            if max_n_accounts and n_accounts_created >= max_n_accounts:
                print(f"already created {max_n_accounts} accounts")
                break

            email = line["Email de la structure"]
            if not email:
                continue

            if limit_to_emails and email not in limit_to_emails:
                continue

            # check if organization for cnfs already exists
            cnfs_id = line["Id du conseiller"]
            if (
                User.objects.filter(email__iexact=email).exists()
                or User.objects.filter(cnfs_id_organization=cnfs_id).exists()
            ):
                print(f"compte déjà créé pour cet {email} - {cnfs_id}")
                continue

            # create account
            user_data = dict(
                email=email,
                password=str(uuid.uuid4()),
                first_name=line["Prénom supérieur hiérarchique"],
                last_name=line["Nom Supérieur hiérarchique"],
                cnfs_id_organization=cnfs_id,
            )
            n_accounts_created += 1
            user = User.objects.create_user(**user_data)
            if cnfs_tag:
                user.tags.add(cnfs_tag)

            # send custom password forgotten email
            form = MyPasswordResetForm(dict(email=email))
            if form.is_valid():
                form.save(
                    email_template_name="email/cnfs/cnfs_organization_account_creation_email.html",
                    subject_template_name="email/cnfs/cnfs_organization_account_creation_subject.txt",
                    domain_override=DOMAIN,
                    extra_email_context={
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    use_https=not IS_LOCAL_DEV,
                )

            print(f"utilisateur {email} - ajouté - user id {user.pk}")


class Command(BaseCommand):
    help = "Import CnFS accounts"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        import_accounts(max_n_accounts=None)
