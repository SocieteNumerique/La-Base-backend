from rest_framework import mixins, viewsets

from main.models import UserSearch
from main.serializers.user_search_serializers import UserSearchSerializer


class UserSearchView(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    def get_queryset(self):
        if (user := self.request.user).is_anonymous:
            return UserSearch.objects.none()
        return UserSearch.objects.filter(user=user)

    serializer_class = UserSearchSerializer
