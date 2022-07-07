from django.contrib.auth.base_user import BaseUserManager
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_email_confirmation(request, user):
    from main.views.user_views import account_activation_token

    current_site = get_current_site(request)
    context = {
        "token": account_activation_token.make_token(user),
        "user": user,
        "domain": current_site.domain,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
    }
    subject = render_to_string("email/validate_email_subject.txt", context)
    subject = "".join(subject.splitlines())
    message = render_to_string(
        "email/validate_email.html",
        context,
    )
    to_email = user.email
    email = EmailMessage(subject, message, to=[to_email])
    email.send()

    return user


def normalize_email(email):
    return BaseUserManager.normalize_email(email)
