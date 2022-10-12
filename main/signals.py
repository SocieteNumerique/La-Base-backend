# delete reverse one to one fields
def gen_delete_one_to_one_parent(attr_name: str):
    def delete_one_to_one_parent(sender, instance, **kwargs):
        if hasattr(instance, attr_name):
            getattr(instance, attr_name).delete()

    return delete_one_to_one_parent


# image crop warmup
def generate_crop(sender, instance, **kwargs):
    instance.warm_cropping()


def delete_images(sender, instance, **kwargs):
    instance.image.delete_all_created_images()
    instance.image.delete(save=False)

    instance.cropped_image.delete_all_created_images()
    instance.cropped_image.delete(save=False)
