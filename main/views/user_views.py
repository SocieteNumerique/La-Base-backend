from django.conf.global_settings import AUTHENTICATION_BACKENDS
from django.contrib.auth import (
    get_user_model,
    authenticate,
    login as django_login,
    logout as django_logout,
)
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.views import PasswordResetConfirmView
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from main.models import User
from main.serializers.user_serializer import (
    UserSerializer,
    ChangePasswordSerializer,
)
from main.user_utils import normalize_email, send_email_confirmation


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_active}"


account_activation_token = TokenGenerator()


class UserView(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    def get_serializer_class(self):
        if self.action == "password":
            return ChangePasswordSerializer
        return UserSerializer

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    @action(detail=True, methods=["PATCH"])
    def password(self, request, pk=None):
        """Update password view."""
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # set_password also hashes the password that the user will get
            user.set_password(serializer.data.get("new_password"))
            user.save()
            response = {
                "status": "success",
                "code": status.HTTP_200_OK,
                "message": "Password updated successfully",
                "data": [],
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"])
    def me(self, request):
        if request.user.is_anonymous:
            return Response(status=400)
        return Response(UserSerializer(request.user).data)

    model = get_user_model()
    serializer_class = UserSerializer


@api_view(["GET"])
def reset_password(request):
    email = request.GET["email"]
    form = PasswordResetForm(dict(email=email))
    if form.is_valid():
        form.save(request=request)
    else:
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_204_NO_CONTENT)


class MyPasswordResetConfirmView(PasswordResetConfirmView):
    def dispatch(self, *args, **kwargs):
        self.request.csrf_processing_done = True
        return super().dispatch(*args, **kwargs)


def send_email_confirmation_view(request, email):
    email = normalize_email(email)
    try:
        user = User.objects.get(email=email)
        send_email_confirmation(request, user)
    except User.DoesNotExist:
        pass
    return HttpResponse()


def activate(_, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect("/?emailConfirmed=true")
    else:
        return HttpResponse("Le lien d'activation n'est pas valide !")


@api_view(["POST"])
def login(request):
    """
    Log in a user

    Args:
        request:
            The request body should contain a JSON object such as::

              {"email": "email@ex.com",
               "password": "secret_pa$$w0rD"}

    Returns:
        JSON object::
            UserSerializer
    """

    data = request.data
    email, password = normalize_email(data["email"]), data["password"]

    try:
        user = User.objects.get(email=email)
        if not user.is_active:
            return Response(
                "Le compte n'a pas été activé. Vérifiez vos mails et cliquez sur le lien de confirmation",
                status=status.HTTP_403_FORBIDDEN,
            )
    except User.DoesNotExist:
        pass

    user = authenticate(email=email, password=password)

    if user is not None:
        user.backend = AUTHENTICATION_BACKENDS[0]
        django_login(request, user)
        return Response(UserSerializer(user).data)
    else:
        return Response(
            "Email et mot de passe ne correspondent pas",
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["POST"])
def logout(request):
    """Log out current user."""
    django_logout(request)
    return Response()
