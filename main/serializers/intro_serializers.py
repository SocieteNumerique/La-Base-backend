from rest_framework import serializers

from main.models import Intro, SeenPageIntros


class IntroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intro
        fields = [
            "html_content",
            "id",
            "image",
            "order",
            "page",
            "position",
            "seen",
            "slug",
            "title",
        ]

    html_content = serializers.SerializerMethodField()
    seen = serializers.SerializerMethodField()

    @staticmethod
    def get_html_content(obj: Intro):
        return obj.content.html

    def get_seen(self, obj: Intro):
        if not (user := getattr(self.context.get("request", {}), "user", None)):
            return False
        if user.is_anonymous:
            return False
        return SeenPageIntros.objects.filter(page=obj.page, user=user).exists()
