
import os
import unittest
from math import degrees

import numpy
from PIL import Image

from autocrop import Background
from autocrop.skew import SkewedImage
from const import IMAGE_PATH

class TestSkewedImage(unittest.TestCase):
    
    def test_skew(self):
        test_image_path = os.path.join(IMAGE_PATH, '6-degrees-skewed.jpg')
        skewed = SkewedImage(Image.open(test_image_path), Background())
        angles = [skewed._get_margin(side)[1] for side in skewed.sides]
        angle = degrees(numpy.median(angles))
        deskewed = skewed.correct()
        width, height = deskewed.size
        
        # The true measurements of the image
        correct_angle = 6.0
        correct_width = 604
        correct_height = 604
        
        self.assertAlmostEqual(angle, correct_angle, delta=0.1)
        self.assertAlmostEqual(correct_width, width, delta=2)
        self.assertAlmostEqual(correct_height, height, delta=2)
        


