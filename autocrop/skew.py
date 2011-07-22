
from PIL import Image

from sampler import PixelSampler
from pixel_math import get_angle, get_median

class SkewedImage(object):
    
    def __init__(self, image, background, precision=8, spread=10):
        self.image = image
        self.width, self.height = image.size
        self.background = background
        self.samples = PixelSampler(image, dpi=1, precision=1)
        self.precision = precision
        self.spread = spread
        self.top = Orientation(
            precision=precision,
            longitudinal=self.height,
            transverse=self.width,
            parallel=self.samples.right,
            perpendicular=self.samples.down
            )
        self.right = Orientation(
            precision=precision,
            longitudinal=self.width,
            transverse=self.height,
            parallel=self.samples.down,
            perpendicular=self.samples.left
            )
        self.bottom = Orientation(
            precision=precision,
            longitudinal=self.height,
            transverse=self.width,
            parallel=self.samples.left,
            perpendicular=self.samples.up
            )
        self.left = Orientation(
            precision=precision,
            longitudinal=self.width,
            transverse=self.height,
            parallel=self.samples.up,
            perpendicular=self.samples.right
            )
    
    def correct(self):
        angles = []
        for side in (self.top, self.right, self.bottom, self.left):
            distances = self._get_side_distances(side)
            angles.append(self._get_angle(distances, side.step))
        angle = get_median(angles)
        image = self.image.rotate(angle, Image.BICUBIC)
        self.samples.image = image
        image = image.crop((
            int(get_median(self._get_side_distances(self.left))),
            int(get_median(self._get_side_distances(self.top))),
            self.width-int(get_median(self._get_side_distances(self.right))),
            self.height-int(get_median(self._get_side_distances(self.bottom)))
            ))
        return image
    
    def _get_side_distances(self, side):
        distances = []
        found_background = False
        for x, y, r, g, b in self.samples.run(side.parallel, side.x, side.y,
                                                side.step, side.count):
            distance = 0
            for x, y, r, g, b in self.samples.run(side.perpendicular, x, y, 1):
                if not found_background:
                    if self.background.matches(r, g, b, self.spread):
                        found_background = True
                else:
                    if not self.background.matches(r, g, b, self.spread):
                        break
                distance += 1
            distances.append(distance)
        return distances
    
    def _get_angle(self, distances, step):
        angles = [get_angle(distances[i+1] - distances[i], step)
                for i in range(len(distances) - 1)]
        return get_median(angles)

class Orientation(object):
    """An object that keeps track of frame-of-reference information.
    """
    def __init__(self, precision, longitudinal, transverse,
            parallel, perpendicular):
        self.precision = precision
        self.longitudinal = longitudinal
        self.transverse = transverse
        self.parallel = parallel
        self.perpendicular = perpendicular
        self.step = transverse / precision
        self.count = self.precision - 2
        if parallel.func_name == 'right':
            self.x = transverse / precision
            self.y = 0
        elif parallel.func_name == 'down':
            self.x = longitudinal - 1
            self.y = transverse / precision
        elif parallel.func_name == 'left':
            self.x = transverse * (precision - 1) / precision
            self.y = longitudinal - 1
        elif parallel.func_name == 'up':
            self.x = 0
            self.y = transverse * (precision - 1) / precision
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
    

