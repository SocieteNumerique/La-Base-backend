from rest_framework import serializers

from main.models import Page


class BasePageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "icon",
            "is_short",
            "html_content",
            "order",
            "show_in_menu",
            "slug",
            "title",
        ]
        abstract = True
        model = Page

    html_content = serializers.SerializerMethodField()

    def get_html_content(self, obj: Page):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(obj.content.html, "html.parser")
        for img in soup.find_all("img"):
            if img.attrs.get("alt"):
                # alt text already exists
                continue
            if not (next_sibling := img.parent.next_sibling):
                continue
            if next_sibling.text.startswith("ALT "):
                alt_text = next_sibling.text.split("ALT ")[1]
                next_sibling.decompose()
                img.attrs["alt"] = alt_text
            else:
                img.attrs["alt"] = ""
        return str(soup)

    is_short = serializers.ReadOnlyField(default=False)


class ShortPageSerializer(BasePageSerializer):
    class Meta(BasePageSerializer.Meta):
        fields = [
            field for field in BasePageSerializer.Meta.fields if field != "html_content"
        ]

    is_short = serializers.ReadOnlyField(default=True)


class FullPageSerializer(BasePageSerializer):
    pass
