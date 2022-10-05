from rest_framework import serializers

from main.models import Page


class BasePageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "title",
            "id",
            "icon",
            "html_content",
            "show_in_menu",
            "is_short",
            "html_content",
        ]
        abstract = True
        model = Page

    html_content = serializers.SerializerMethodField()

    def get_html_content(self, obj: Page):
        return obj.content.html

    is_short = serializers.ReadOnlyField(default=False)


class ShortPageSerializer(BasePageSerializer):
    class Meta(BasePageSerializer.Meta):
        fields = [
            field for field in BasePageSerializer.Meta.fields if field != "html_content"
        ]

    is_short = serializers.ReadOnlyField(default=True)


class FullPageSerializer(BasePageSerializer):
    pass
