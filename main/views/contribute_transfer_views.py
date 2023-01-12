from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpResponse
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from main.models import Resource, Base
from main.query_changes.permissions import resources_queryset_for_user

SUGGESTION_BODY = """Bonjour,

{name} ({email}) a une suggestion à faire concernant la fiche ressource {resource_title} que vous avez publié sur La Base, voici son message :

{message}

Suivez ce lien pour accéder directement à l’édition de la fiche : {resource_url}

Vous pouvez également répondre directement à {name} à cette adresse mail {email}.

Cordialement,
L’équipe de La Base
"""
CONTRIBUTOR_BODY = """Bonjour,

{name} ({email}) voudrait être contributeur de votre fiche ressource {resource_title} que vous avez publié sur La Base, voici son message :

{message}

Pour l'ajouter en contributeur, suivez ce lien suivant pour accéder directement à l’édition de la fiche et allez dans l'onglet "contributeurs" : {resource_url}

Vous pouvez également répondre directement à {name} à cette adresse mail {email}.

Cordialement,
L’équipe de La Base
"""
ADMINISTRATOR_BODY = """Bonjour,

{name} ({email}) voudrait être administrateur de votre fiche ressource {resource_title} que vous avez publié sur La Base, voici son message :

{message}

Si vous acceptez, vous pouvez cliquer sur le lien ci dessous pour accepter sa demande.
Attention, cette action est irréversible, en cliquant sur ce lien vos droits d’administration seront immédiatement transférés à cette personne, et la fiche ressource disparaîtra de votre base. Vous ne pourrez plus l’éditer à moins d’être nommé contributeur.

Lien de validation immédiate de transfert de la fiche {resource_title} : {resource_transfer_link}

Vous pouvez également répondre directement à {name} à cette adresse mail {email}.

Cordialement,
L’équipe de La Base
"""
MESSAGE_SUBJECT = (
    "La Base [Suggestion d’un utilisateur à propos d’une de vos fiches ressources]"
)


class ContributeView(APIView):
    def post(self, request):
        if request.user.is_anonymous:
            return HttpResponse(status=403)

        id_ = request.data["id"]
        contribute_choice = request.data["contribute_choice"]
        message = request.data["message"]
        target_base = request.data.get("target_base")

        try:
            # if user has no access to that resource, he cannot contact the owner
            resource = resources_queryset_for_user(request.user).get(pk=id_)
        except Resource.DoesNotExist:
            return HttpResponse(status=403)

        current_site = get_current_site(request)
        domain = current_site.domain
        resource_url = f"http://{domain}/ressource/{id_}/edition"

        resource_title = resource.title
        recipient = resource.root_base.owner.email

        if contribute_choice == "administrator":
            resource_transfer_link = f"http://{domain}" + reverse(
                "transfer", args=[resource.pk, target_base]
            )
        else:
            resource_transfer_link = None

        if contribute_choice == "suggestion":
            body = SUGGESTION_BODY
        elif contribute_choice == "contributor":
            body = CONTRIBUTOR_BODY
        elif contribute_choice == "administrator":
            body = ADMINISTRATOR_BODY
        else:
            raise ValidationError(f"Wrong contribute_choice: was {contribute_choice}")
        name = f"{request.user.first_name} {request.user.last_name}"

        send_mail(
            MESSAGE_SUBJECT,
            body.format(
                email=request.user.email,
                name=name,
                resource_url=resource_url,
                resource_title=resource_title,
                resource_transfer_link=resource_transfer_link,
                message=message,
            ),
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
        )

        return HttpResponse()


NOT_OWNER_MESSAGE = "Erreur : Vous n'êtes pas le propriétaire de cette fiche. Pour faire le transfert, vous devez cliquer sur le lien en étant connecté en tant que le propriétaire de la fiche."
TARGET_BASE_DOES_NOT_EXIST = (
    "Erreur : La Base cible n'existe pas ou plus. Vous pouvez ignorer cette demande."
)
SUCCESS_MESSAGE = "Le changement de propriétaire de la fiche ressource {resource_title} bien été effectué."


class TransferView(APIView):
    def get(self, request, resource_id, target_base: int):
        try:
            resource = Resource.objects.get(pk=resource_id)
        except Resource.DoesNotExist:
            return HttpResponse("Cette fiche ressource n'existe plus", status=404)

        if resource.root_base.owner != request.user:
            return HttpResponse(
                NOT_OWNER_MESSAGE.format(resource_owner_email=resource.root_base.owner),
                status=403,
            )

        try:
            target_base = Base.objects.get(pk=target_base)
        except Base.DoesNotExist:
            return HttpResponse(TARGET_BASE_DOES_NOT_EXIST, status=403)

        resource.root_base = target_base
        resource.save()

        return HttpResponse(
            SUCCESS_MESSAGE.format(resource_title=resource.title), status=200
        )
