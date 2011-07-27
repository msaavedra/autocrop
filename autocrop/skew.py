# Copyright 2011 Michael Saavedra

from PIL.Image import BICUBIC

from sampler import PixelSampler
from pixel_math import get_angle, get_median

# This value works well in all situations, so no need to make it configurable.
PRECISION = 8

class SkewedImage(object):
    
    def __init__(self, image, background, contrast=10):
        self.image = image
        self.width, self.height = image.size
        self.background = background
        self.contrast = contrast
        sampler = PixelSampler(image, dpi=1, precision=1)
        self.left = Left(sampler)
        self.top = Top(sampler)
        self.right = Right(sampler)
        self.bottom = Bottom(sampler)
    
    def correct(self, margin_limit):
        margins = []
        angles = []
        for side in (self.left, self.top, self.right, self.bottom):
            distance, angle = self._get_margin(side, margin_limit)
            margins.append(distance)
            angles.append(angle)
        margins[2] = self.width - margins[2]
        margins[3] = self.height - margins[3]
        return self.image.rotate(get_median(angles), BICUBIC).crop(margins)
    
    def _get_margin(self, side, margin_limit):
        distances = []
        for x, y, r, g, b in side.run_parallel():
            distance = 0
            found_background = False
            for x, y, r, g, b in side.run_perpendicular(x, y):
                if not found_background:
                    if self.background.matches(r, g, b, self.contrast):
                        found_background = True
                else:
                    if not self.background.matches(r, g, b, self.contrast):
                        break
                distance += 1
                if distance > margin_limit:
                    # If we've come to this, the margin detection has
                    # certainly failed. The safest thing to do is report
                    # no margin at all
                    distance = 0
                    break
            distances.append(distance)
        angles = [get_angle(distances[i+1] - distances[i], side.step)
                    for i in range(len(distances) - 1)]
        return int(get_median(distances)), get_median(angles)


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

class Right(Top):
    
    def __init__(self, sampler):
        self.sampler = sampler
        self.step = sampler.height / self.precision
        self.parallel = sampler.down
        self.perpendicular = sampler.left
        self.x = sampler.width - 1
        self.y = self.step

class Bottom(Top):
    
    def __init__(self, sampler):
        self.sampler = sampler
        self.step = sampler.width / self.precision
        self.parallel = sampler.left
        self.perpendicular = sampler.up
        self.x = sampler.width - self.step
        self.y = sampler.height - 1

class Left(Top):
    
    def __init__(self, sampler):
        self.sampler = sampler
        self.step = sampler.height / self.precision
        self.parallel = sampler.up
        self.perpendicular = sampler.right
        self.x = 0
        self.y = sampler.height - self.step


if __name__ == '__main__':
    from background import Background
    from PIL import Image
    background = Background()
    image = Image.open('/home/mike/skew_test.png')
    skew = SkewedImage(image, background)
    image = skew.correct(margin_limit=80)
    image.show()
    

