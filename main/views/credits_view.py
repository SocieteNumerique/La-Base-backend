from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpResponse
from rest_framework.views import APIView

from main.models import Resource
from main.query_changes.permissions import resources_queryset_for_user


MESSAGE_BODY = """Bonjour,

{name} ({email}) voudrait être crédité sur votre fiche ressource {resource_title}, voici son message :

{message}

Vous pouvez suivre ce lien pour modifier la fiche et ajouter son profil à la liste des producteurs dans l’onglet “crédits” : {resource_url}

Vous pouvez également répondre directement par mail à {name} à {email}.

Cordialement,
L’équipe de La Base
"""


class CreditsView(APIView):
    def post(self, request):
        if request.user.is_anonymous:
            return HttpResponse(status=403)

        id_ = request.data["id"]

        try:
            # if user has no access to that resource, he cannot contact the owner
            resource = resources_queryset_for_user(request.user).get(pk=id_)
        except Resource.DoesNotExist:
            return HttpResponse(status=403)

        message = request.data["message"]

        current_site = get_current_site(request)
        domain = current_site.domain
        resource_url = f"http://{domain}/ressource/{id_}/edition"
        resource_title = f"http://{domain}/ressource/{id_}/"
        recipient = resource.root_base.owner.email

        name = f"{request.user.first_name} {request.user.last_name}"

        send_mail(
            f"[La Base - Demande de crédit] - {resource.title} ({id_})",
            MESSAGE_BODY.format(
                email=request.user.email,
                name=name,
                resource_url=resource_url,
                resource_title=resource_title,
                message=message,
            ),
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
        )

        return HttpResponse()
