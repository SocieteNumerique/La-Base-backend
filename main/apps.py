from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from moine_back.settings import (
    ONE_TO_ONE_FIELD_REVERSE_DELETE,
)


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

    def ready(self):
        # delete reverse one to one fields
        for (model_name, attr_name) in ONE_TO_ONE_FIELD_REVERSE_DELETE:

            @receiver(post_delete, sender=self.get_model(model_name))
            def delete_one_to_one_parent(sender, instance, **kwargs):
                if hasattr(instance, attr_name):
                    getattr(instance, attr_name).delete()

        # image crop warmup
        @receiver(post_save, sender=self.get_model("ResizableImage"))
        def generate_crop(sender, instance, **kwargs):
            instance.warm_cropping()
