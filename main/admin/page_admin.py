from django.contrib import admin, messages

from main.models.page import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "show_in_menu")

    def save_model(self, request, obj: Page, form, change):
        """Check all images have an alt text."""
        from bs4 import BeautifulSoup

        super().save_model(request, obj, form, change)
        obj.refresh_from_db()

        soup = BeautifulSoup(obj.content.html, "html.parser")
        missing_alt_texts = 0
        for img in soup.find_all("img"):
            if not img.attrs.get("alt") and not (
                img.parent.next_sibling
                and img.parent.next_sibling.text.startswith("ALT ")
            ):
                missing_alt_texts += 1
                continue
        if missing_alt_texts:
            messages.error(
                request,
                f"{missing_alt_texts} images sans texte alternatif. Pour ajouter un texte alternatif à une image, il suffit d'écrire `ALT mon texte alternatif` juste en-dessous de l'image. Bien commencer le text par `ALT` !",
            )
