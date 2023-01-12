from django.db import models
from django.utils.safestring import mark_safe
from django_quill.fields import QuillField

POSITION_CHOICES = [
    ["top", "au-dessus"],
    ["bottom", "en-dessous"],
    ["right", "à droite"],
    ["left", "à gauche"],
]

IGNORED = (
    "; les éléments commençant par"
    "<pre style='display:inline;padding:2px 4px;background:#e9e9e9'>draft</pre>"
    "sont ignorés."
)


class Intro(models.Model):
    class Meta:
        ordering = ("order",)
        verbose_name = "bulle de didacticiel"
        verbose_name_plural = "bulles de didacticiel"

    title = models.CharField(verbose_name="titre", max_length=100)
    content = QuillField(verbose_name="contenu")
    order = models.IntegerField(verbose_name="ordre dans la page")
    slug = models.CharField(
        verbose_name="identifiant",
        max_length=50,
        help_text=mark_safe(
            f"<b>Confirmer avec les devs avant changement ou ajout !</b> Si plusieurs bulles s'appliquent au même contenu, mettre deux fois le même identifiant. {IGNORED}"
        ),
    )
    image = models.ImageField(
        blank=True,
        null=True,
        help_text="Mettre une image légère, de largeur min 310px, max 620px",
    )
    position = models.CharField(
        choices=POSITION_CHOICES, default="bottom", max_length=6
    )

    def __str__(self):
        return self.title
