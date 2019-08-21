# Copyright 2011 Michael Saavedra

from math import atan2, degrees

import numpy
from PIL.Image import BICUBIC

from .sampler import PixelSampler


class SkewedImage(object):
    
    def __init__(self, image, background, contrast=10):
        self.image = image
        self.width, self.height = image.size
        self.background = background
        self.contrast = contrast
        sampler = PixelSampler(image, dpi=1, precision=1)
        self.sides = (
            Left(sampler),
            Top(sampler),
            Right(sampler),
            Bottom(sampler),
            )
    
    def correct(self):
        margins, angles = list(
            zip(*[self._get_margin(side) for side in self.sides])
            )
        rotated_img = self.image.rotate(degrees(numpy.median(angles)), BICUBIC)
        return rotated_img.crop(margins)
    
    def _get_margin(self, side):
        """Find the distance and angle of the margin on a particular side.
        """
        distances = []
        angles = []
        for start_x, start_y, _, _, _ in side.run_parallel():
            samples = side.run_perpendicular(start_x, start_y)
            
            x = start_x
            y = start_y
            
            # First try to find any shadows along the image border.
            for x, y, r, g, b in samples:
                if self.background.matches((r, g, b), self.contrast):
                    break
                if side.get_distance(x, y) > side.step:
                    # We've gone too far. Reset.
                    samples = side.run_perpendicular(start_x, start_y)
                    break
            
            # Next try to find any remaining background.
            for x, y, r, g, b in samples:
                if not self.background.matches((r, g, b), self.contrast):
                    break
            
            if distances:
                angles.append(side.get_angle(distances[-1], x, y))
            distances.append(side.get_distance(x, y))
        
        return int(numpy.median(distances)), numpy.median(angles)


class Top(object):
    
    precision = 6
    count = precision - 2
    
    def __init__(self, sampler):
        self.sampler = sampler
        self.step = sampler.width / self.precision
        self.parallel = sampler.right
        self.perpendicular = sampler.down
        self.x = self.step
        self.y = 0
    
    def run_parallel(self):
        return self.sampler.run(
            self.parallel, self.x, self.y, self.step, self.count
            )
    
    def run_perpendicular(self, x, y):
        return self.sampler.run(self.perpendicular, x, y, 1)
    
    def get_distance(self, x, y):
        return y
    
    def get_angle(self, prev_distance, x, y):
        return atan2(y - prev_distance, self.step)


class Right(Top):
    
    def __init__(self, sampler):
        self.sampler = sampler
        self.step = sampler.height / self.precision
        self.parallel = sampler.down
        self.perpendicular = sampler.left
        self.x = sampler.width - 1
        self.y = self.step
    
    def get_distance(self, x, y):
        return x
    
    def get_angle(self, prev_distance, x, y):
        return atan2(prev_distance - x, self.step)


class Bottom(Top):
    
    def __init__(self, sampler):
        self.sampler = sampler
        self.step = sampler.width / self.precision
        self.parallel = sampler.left
        self.perpendicular = sampler.up
        self.x = sampler.width - self.step
        self.y = sampler.height - 1
    
    def get_distance(self, x, y):
        return y
    
    def get_angle(self, prev_distance, x, y):
        return atan2(prev_distance - y, self.step)


class Left(Top):
    
    def __init__(self, sampler):
        self.sampler = sampler
        self.step = sampler.height / self.precision
        self.parallel = sampler.up
        self.perpendicular = sampler.right
        self.x = 0
        self.y = sampler.height - self.step
    
    def get_distance(self, x, y):
        return x
        
    def get_angle(self, prev_distance, x, y):
        return atan2(x - prev_distance, self.step)
