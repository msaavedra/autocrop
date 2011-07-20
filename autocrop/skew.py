
from PIL import Image

from sampler import PixelSampler
from pixel_math import get_angle, get_median, get_adjacent

class Skew(object):
    
    def __init__(self, image, background):
        self.image = image
        self.width, self.height = image.size
        self.background = background
        self.samples = PixelSampler(image, dpi=1, precision=1)
        self.top_angle, self.top_margin = self._measure_side(
            x=self.width/8,
            y=0,
            length=self.width,
            drop=self.height,
            lateral=self.samples.right,
            inward=self.samples.down
            )
        self.right_angle, self.right_margin = self._measure_side(
            x=self.width-1,
            y=self.height/8,
            length=self.height,
            drop=self.width,
            lateral=self.samples.down,
            inward=self.samples.left
            )
        self.bottom_angle, self.bottom_margin = self._measure_side(
            x=self.width*7/8,
            y=self.height-1,
            length=self.width,
            drop=self.height,
            lateral=self.samples.left,
            inward=self.samples.up
            )
        self.left_angle, self.left_margin = self._measure_side(
            x=0,
            y=self.height*7/8,
            length=self.height,
            drop=self.width,
            lateral=self.samples.up,
            inward=self.samples.right
            )
    
    def correct(self):
        angle = get_median([
            self.top_angle, self.right_angle,
            self.bottom_angle, self.left_angle
            ])
        image = self.image.rotate(angle, Image.BICUBIC)
        image = image.crop((
            self.left_margin,
            self.top_margin,
            self.width-self.right_margin,
            self.height-self.bottom_margin
            ))
        return image
    
    def _measure_side(self, x, y, length, drop, lateral, inward):
        distance = length / 8
        count = 5 # This should always be an odd number.
        depths = []
        for x1, y1, r, g, b in self.samples.run(lateral, x, y, distance, count):
            if self.background.matches(r, g, b, 15):
                found_background = True
            else:
                found_background = False
            depth = 0
            for x2, y2, r, g, b in self.samples.run(inward, x1, y1, 1):
                depth += 1
                if not found_background:
                    if self.background.matches(r, g, b, 15):
                        found_background = True
                else:
                    if not self.background.matches(r, g, b, 15):
                        break
            depths.append(depth)
        angles = [get_angle(depths[i+1] - depths[i], distance)
                for i in range(len(depths) - 1)]
        angle = get_median(angles)
        center_depth = depths[count/2]
        hypotenuse = drop / 2 - center_depth
        adjacent = get_adjacent(angle, hypotenuse)
        margin = drop / 2 - adjacent
        return angle, margin


if __name__ == '__main__':
    from background import Background
    from PIL import Image
    background = Background()
    image = Image.open('/home/mike/skew_test2.png')
    skew = Skew(image, background)
    image = skew.correct()

