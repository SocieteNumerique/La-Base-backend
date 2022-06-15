from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from main.serializers.user_serializer import UserSerializer, ChangePasswordSerializer


class UserView(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    def get_serializer_class(self):
        if self.action == "create":
            return UserSerializer
        elif self.action == "password":
            return ChangePasswordSerializer

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
