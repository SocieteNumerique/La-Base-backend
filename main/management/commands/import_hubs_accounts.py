import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.core.management import BaseCommand

from main.models import Tag
from main.models.user import User
from main.serializers.user_serializer import (
    HUBS_RESERVED_TAG_NAME,
)
from moine_back.settings import BASE_DIR, DOMAIN, IS_LOCAL_DEV

from csv import DictReader

source_file_path = BASE_DIR / "annuaire_des_Hubs.csv"
UserModel = get_user_model()


class Command(BaseCommand):
    help = "Import hub accounts"

    def add_arguments(self, parser):
        pass

    def import_accounts(self, limit_to_emails=None, max_n_accounts=None):
        with open(source_file_path) as fh:
            reader = DictReader(fh, delimiter=",")

            try:
                hub_tag = Tag.objects.get(name=HUBS_RESERVED_TAG_NAME)
            except Tag.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"tag des hubs non trouvé. Créez un tag nommé '{HUBS_RESERVED_TAG_NAME}'"
                    )
                )
                return

            n_accounts_created = 0
            n_accounts_found = 0
            for line in reader:
                if max_n_accounts and n_accounts_created >= max_n_accounts:
                    print(f"already created {max_n_accounts} accounts")
                    break

                email = line["email"]
                if not email:
                    continue

                if limit_to_emails and email not in limit_to_emails:
                    continue

                # check if user already exists
                if User.objects.filter(email=email).exists():
                    print(f"compte déjà créé pour cet {email}")
                    n_accounts_found += 1
                    user = User.objects.get(email=email)
                    user.tags.add(hub_tag)
                    continue

                # create account
                user_data = dict(
                    email=line["email"],
                    password=str(uuid.uuid4()),
                    first_name=line["prenom"],
                    last_name=line["nom"],
                    is_active=True,
                )
                n_accounts_created += 1
                user = User.objects.create_user(**user_data)
                if hub_tag:
                    user.tags.add(hub_tag)

                print(f"utilisateur {email} ajouté")

                # send custom password forgotten email
                form = PasswordResetForm(dict(email=email))
                if form.is_valid():
                    form.save(
                        email_template_name="email/cnfs/hubs_account_creation_email.html",
                        subject_template_name="email/cnfs/hubs_account_creation_subject.txt",
                        domain_override=DOMAIN,
                        extra_email_context={
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                        },
                        use_https=not IS_LOCAL_DEV,
                    )
                    print(f"email de modification de mdp envoyé pour {email}")
                else:
                    print(f"formulaire invalide pour {email} : mail non envoyé")

            self.stdout.write(
                self.style.SUCCESS(
                    f"{n_accounts_created + n_accounts_found} comptes créés, dont {n_accounts_found} déjà présents"
                )
            )

    def handle(self, *args, **options):
        self.import_accounts(max_n_accounts=(1 if IS_LOCAL_DEV else None))
