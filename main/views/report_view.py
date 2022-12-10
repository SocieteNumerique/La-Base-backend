from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpResponse
from rest_framework.views import APIView


class ReportView(APIView):
    def post(self, request):
        instance_type: str = request.data["instance_type"]
        id_ = request.data["id"]
        motive = request.data["motive"]
        description = request.data["description"]
        if request.user.is_anonymous:
            show_user = "un utilisateur anonyme"
        else:
            show_user = request.user.email

        current_site = get_current_site(request)
        domain = current_site.domain
        resource_url = (
            f"http://{domain}/admin/main/{instance_type.lower()}/{id_}/change/"
        )

        send_mail(
            f"[La Base - Signalement] - {instance_type} {id_} - {motive}",
            f"Envoyé par {show_user}\n\nLien vers la {instance_type}: {resource_url}"
            f"\n\nMessage de l'utilisateur :\n\n{description}",
            settings.DEFAULT_FROM_EMAIL,
            settings.SEND_REPORTS_TO,
        )

        return HttpResponse()
