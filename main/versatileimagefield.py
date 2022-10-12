from io import BytesIO

from versatileimagefield.datastructures import SizedImage
from versatileimagefield.registry import versatileimagefield_registry


class ToWidthImage(SizedImage):
    filename_key = "to-width"

    def process_image(self, image, image_format, save_kwargs, width, height):
        """
        Returns a BytesIO instance of `image` that will resize to width and keep proportions
        """
        image_file = BytesIO()
        calc_height = round(image.height * width / image.width)
        res = image.resize((width, calc_height))
        res.save(image_file, **save_kwargs)
        return image_file


class ToHeightImage(SizedImage):
    filename_key = "to-height"

    def process_image(self, image, image_format, save_kwargs, width, height):
        """
        Returns a BytesIO instance of `image` that will resize to height and keep proportions`
        """
        image_file = BytesIO()
        calc_width = image.width * height / image.height
        res = image.resize((width, calc_width))
        res.save(image_file, **save_kwargs)
        return image_file


versatileimagefield_registry.register_sizer("to-height", ToHeightImage)
versatileimagefield_registry.register_sizer("to-width", ToWidthImage)
