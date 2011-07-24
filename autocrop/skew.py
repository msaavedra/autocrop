# Copyright 2011 Michael Saavedra

from PIL import Image

from sampler import PixelSampler
from pixel_math import get_angle, get_median

# This value works well in all situations, so no need to make it configurable.
PRECISION = 8

class SkewedImage(object):
    
    def __init__(self, image, background, contrast=10):
        self.image = image
        self.width, self.height = image.size
        self.background = background
        self.samples = PixelSampler(image, dpi=1, precision=1)
        self.contrast = contrast
        self.top = Orientation(
            longitudinal=self.height,
            transverse=self.width,
            parallel=self.samples.right,
            perpendicular=self.samples.down
            )
        self.right = Orientation(
            longitudinal=self.width,
            transverse=self.height,
            parallel=self.samples.down,
            perpendicular=self.samples.left
            )
        self.bottom = Orientation(
            longitudinal=self.height,
            transverse=self.width,
            parallel=self.samples.left,
            perpendicular=self.samples.up
            )
        self.left = Orientation(
            longitudinal=self.width,
            transverse=self.height,
            parallel=self.samples.up,
            perpendicular=self.samples.right
            )
    
    def correct(self):
        angles = []
        for side in (self.top, self.right, self.bottom, self.left):
            distances = self._get_margin_distances(side)
            angles.extend(self._get_margin_angles(distances, side.step))
        angle = get_median(angles)
        
        image = self.image.convert('RGBA').rotate(angle, Image.BICUBIC)
        rgba = (
            int(self.background.medians['red']),
            int(self.background.medians['green']),
            int(self.background.medians['blue']),
            255 # alpha value - completely opaque
            )
        bg = Image.new('RGBA', image.size, rgba)
        image = Image.composite(image, bg, image).convert(self.image.mode)
        
        self.samples.update_image(image)
        image = image.crop((
            int(get_median(self._get_margin_distances(self.left))),
            int(get_median(self._get_margin_distances(self.top))),
            self.width-int(get_median(self._get_margin_distances(self.right))),
            self.height-int(get_median(self._get_margin_distances(self.bottom)))
            ))
        return image
    
    def _get_margin_distances(self, side):
        step = side.transverse / PRECISION
        count = PRECISION - 2
        distances = []
        for p in self.samples.run(side.parallel, side.x, side.y, step, count):
            x, y = p[:2]
            distance = 0
            found_background = False
            for x, y, r, g, b in self.samples.run(side.perpendicular, x, y, 1):
                if not found_background:
                    if self.background.matches(r, g, b, self.contrast):
                        found_background = True
                    elif distance >= (step / 4):
                        distance = 0
                        break
                else:
                    if not self.background.matches(r, g, b, self.contrast):
                        break
                distance += 1
            distances.append(distance)
        return distances
    
    def _get_margin_angles(self, distances, step):
        return [get_angle(distances[i+1] - distances[i], step)
                for i in range(len(distances) - 1)]

class Orientation(object):
    """An object that keeps track of frame-of-reference information.
    """
    def __init__(self, longitudinal, transverse, parallel, perpendicular):
        self.longitudinal = longitudinal
        self.transverse = transverse
        self.parallel = parallel
        self.perpendicular = perpendicular
        if parallel.func_name == 'right':
            self.x = transverse / PRECISION
            self.y = 0
        elif parallel.func_name == 'down':
            self.x = longitudinal - 1
            self.y = transverse / PRECISION
        elif parallel.func_name == 'left':
            self.x = transverse * (PRECISION - 1) / PRECISION
            self.y = longitudinal - 1
        elif parallel.func_name == 'up':
            self.x = 0
            self.y = transverse * (PRECISION - 1) / PRECISION
        else:
            msg = 'Invalid parallel function name %s.' % parallel.func_name
            raise StandardError(msg)


if __name__ == '__main__':
    from background import Background
    from PIL import Image
    background = Background()
    image = Image.open('/home/mike/skew_test2.png')
    skew = SkewedImage(image, background)
    image = skew.correct()
    image.show()
    

