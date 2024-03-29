from django.apps import AppConfig
from django.db.models.signals import post_delete, pre_delete

from moine_back.settings import (
    ONE_TO_ONE_FIELD_REVERSE_DELETE,
)


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

    def ready(self):
        from . import signals

        # delete reverse one to one fields
        for (model_name, attr_name) in ONE_TO_ONE_FIELD_REVERSE_DELETE:
            post_delete.connect(
                signals.gen_delete_one_to_one_parent(attr_name),
                sender=self.get_model(model_name),
            )

        pre_delete.connect(
            signals.delete_images, sender=self.get_model("ResizableImage")
        )
