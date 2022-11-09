from rest_framework import serializers

from main.models import TextBlock


class TextBlockSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "html_content",
            "slug",
        ]
        model = TextBlock

    html_content = serializers.SerializerMethodField()

    @staticmethod
    def get_html_content(obj: TextBlock):
        return obj.content.html
