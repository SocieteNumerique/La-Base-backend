from django.db.models.signals import pre_save
from django.dispatch import receiver

from main.models import Base


# delete reverse one to one fields
def gen_delete_one_to_one_parent(attr_name: str):
    def delete_one_to_one_parent(sender, instance, **kwargs):
        if hasattr(instance, attr_name):
            getattr(instance, attr_name).delete()

    return delete_one_to_one_parent


def delete_images(sender, instance, **kwargs):
    instance.image.delete_all_created_images()
    instance.image.delete(save=False)

    instance.cropped_image.delete_all_created_images()
    instance.cropped_image.delete(save=False)


@receiver(pre_save, sender=Base)
def set_contact_state(sender, instance, **kwargs):
    if instance.contact_state is None:
        instance.contact_state = instance.state
    if instance.state == "private":
        instance.contact_state = "private"
