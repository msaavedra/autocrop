# Copyright 2011 Michael Saavedra

import sys

import numpy

from sampler import PixelSampler


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
                'red': 1.5,
                'green': 1.5,
                'blue': 1.5,
                }
    
    def load_from_image(self, image, dpi):
        """Determine background stats by examining a blank scan.
        """
        sampler = PixelSampler(image, dpi, precision=4)
        reds, greens, blues = zip(*[sample[2:] for sample in sampler])
        self.medians = {
            'red': numpy.median(reds),
            'green': numpy.median(greens),
            'blue': numpy.median(blues),
            }
        self.std_devs = {
            'red': numpy.std(reds),
            'green': numpy.std(greens),
            'blue': numpy.std(blues),
            }
        return self
    
    def matches(self, red, green, blue, spread):
        """Return True if the given color is probably part of the background.
        """
        values = {'red': red, 'green': green, 'blue': blue}
        for color in ('red', 'green', 'blue'):
            delta = abs(self.medians[color] - values[color])
            if delta > self.std_devs[color] * spread:
                return False
        return True


