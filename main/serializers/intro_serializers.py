from rest_framework import serializers

from main.models import Intro


class IntroSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "id",
            "title",
            "html_content",
            "order",
            "slug",
            "page",
            "image",
            "position",
        ]
        model = Intro

    html_content = serializers.SerializerMethodField()

    @staticmethod
    def get_html_content(obj: Intro):
        return obj.content.html
