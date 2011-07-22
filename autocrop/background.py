
import sys

from cross_platform import files

from sampler import PixelSampler
from pixel_math import get_median, get_standard_deviation

class Background(object):
    
    def __init__(self, medians=None, std_devs=None):
        # If stats aren't available use some reasonable defaults (almost
        # white with some variation).
        if medians:
            self.medians = medians
        else:
            self.medians = {
                'red': 245.0,
                'green': 245.0,
                'blue': 245.0,
                }
        if std_devs:
            self.std_devs = std_devs
        else:
            self.std_devs = {
                'red': 2.0,
                'green': 2.0,
                'blue': 2.0,
                }
    
    def load_from_image(self, image, dpi):
        """Determine background stats by examining a blank scan.
        """
        seq_red = []
        seq_green = []
        seq_blue = []
        for (x, y, red, green, blue) in PixelSampler(image, dpi, precision=4):
            seq_red.append(red)
            seq_green.append(green)
            seq_blue.append(blue)
        self.medians = {
            'red': get_median(seq_red),
            'green': get_median(seq_green),
            'blue': get_median(seq_blue),
            }
        self.std_devs = {
            'red': get_standard_deviation(seq_red),
            'green': get_standard_deviation(seq_green),
            'blue': get_standard_deviation(seq_blue),
            }
    
    def load_stats(self, medians, std_devs):
        self.medians = medians
        self.std_devs = std_devs
    
    def matches(self, red, green, blue, spread):
        """Return True if the given color is probably part of the background.
        """
        values = vars()
        for color in ('red', 'green', 'blue'):
            delta = abs(self.medians[color] - values[color])
            if delta > self.std_devs[color] * spread:
                return False
        return True


