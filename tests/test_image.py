
import os
import unittest

from PIL import Image

from autocrop import MultiPartImage, Background
from const import IMAGE_PATH

class TestImage(unittest.TestCase):
    
    def setUp(self):
        test_image_path = os.path.join(IMAGE_PATH, '72-dpi-4-images.jpg')
        image = Image.open(test_image_path)
        self.images = MultiPartImage(
            image, Background(), dpi=72, deskew=False, precision=4
            )
    
    def test_images(self):
        self.assertEqual(len(self.images), 4)
        # The  maximum size of the margin around the cropped sections.
        margin = (self.images.dpi / self.images.precision) * 2
        # The correct sizes of the sections, measured directly from the image.
        sizes = [
            (280, 165),
            (240, 200),
            (550, 200),
            (550, 283),
            ]
        for image in self.images:
            correct_width, correct_height = sizes.pop(0)
            width, height = image.size
            self.assertAlmostEqual(correct_width, width, delta=margin)
            self.assertAlmostEqual(correct_height, height, delta=margin)


