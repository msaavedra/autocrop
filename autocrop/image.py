# Copyright 2011 Michael Saavedra

from sampler import PixelSampler
from skew import SkewedImage


class MultiPartImage(object):
    """Object for handling images that contain multiple subimages.
    
    This is used, for example, to detect and access multiple photos that were
    scanned simultaneously in a flat-bed scanner. """
    def __init__(self, image, background, dpi, precision=16,
            deskew=True, contrast=10):
        self.contrast = contrast
        self.image = image
        self.dpi = dpi
        self.width, self.height = image.size
        self.precision = precision
        self.deskew = deskew
        self.samples = PixelSampler(image, dpi, precision)
        self.background = background
        self.sections = self._find_sections()
    
    def __iter__(self):
        for section in self.sections:
            image = self.image.crop(
                (section.left, section.top, section.right, section.bottom)
                )
            if self.deskew:
                skew = SkewedImage(image, self.background, self.contrast)
                image = skew.correct()
            yield image
    
    def __len__(self):
        return len(self.sections)
    
    def _find_sections(self):
        sections = []
        for (x, y, red, green, blue) in self.samples:
            # Skip if the sample is background or is already in a section.
            if self.background.matches(red, green, blue, self.contrast):
                continue
            if True in (section.contains(x,y) for section in sections):
                continue
            
            # Find contiguous samples. This works like a 4-way flood fill, but
            # instead of changing the color we just collect the coordinates.
            seeds = [(x, y)]
            pixels = set(seeds)
            for coords in iter(seeds):
                for x, y, r, g, b in self.samples.around(*coords):
                    if (x, y) not in pixels:
                        pixels.add((x, y))
                        if not self.background.matches(r, g, b, self.contrast):
                            seeds.append((x, y))
            new_section = ImageSection(pixels)
            
            if True in (s.merge_if_overlapping(new_section) for s in sections):
                continue
            
            sections.append(new_section)
        
        # Filter out sections smaller than 1 sqaure inch before returning.
        return [s for s in sections if s > self.dpi ** 2]


class ImageSection(object):
    """A rectangular area wholly contained within an image
    """
    def __init__(self, pixels):
        """Create a new section instance.
        
        The dimensions will be the smallest possible that can contain the
        provided sequence of pixels (each of which is an x, y tuple).
        """
        seq_x, seq_y = zip(*pixels)
        self.left = min(seq_x)
        self.right = max(seq_x)
        self.top = min(seq_y)
        self.bottom = max(seq_y)
        self.height = self.bottom - self.top
        self.width = self.right - self.left
        self.area = self.height * self.width
    
    def contains(self, x, y):
        """Returns True only if the given coordinate is inside this photo.
        """
        if (self.left <= x <= self.right) and (self.top <= y <= self.bottom):
            return True
        else:
            return False
    
    def __contains__(self, pixel):
        return self.contains(*pixel)
    
    def overlap(self, other):
        """Determine the degree of overlap between this section and another.
        
        The return value is a float from 0 to 1.0 describing how much of the
        smaller section is overlapping the larger one.  A value of 0 means the
        two are non-overlapping, while 1.0 means that the smaller is completely
        contained by the larger.
        """
        if (self.top > other.bottom):
            return 0.0
        if (self.bottom < other.top):
            return 0.0
        if (self.right < other.left):
            return 0.0
        if (self.left > other.right):
            return 0.0
        else:
            height = min(self.right, other.right) - max(self.left, other.left)
            width = min(self.bottom, other.bottom) - max(self.top, other.top)
            overlap_area = height * width
            smaller = min(self.height * self.width, other.height * other.width)
            return float(overlap_area) / smaller
    
    def merge(self, other, overlap):
        self.top = min(self.top, other.top)
        self.bottom = max(self.bottom, other.bottom)
        self.left = min(self.left, other.left)
        self.right = max(self.right, other.right)
        self.height = self.bottom - self.top
        self.width = self.right - self.left
        unoverlapped = int(min(self.area, other.area) * (1 - overlap))
        self.area = max(self.area, other.area) + unoverlapped
    
    def merge_if_overlapping(self, other, margin=.15):
        overlap = self.overlap(other)
        if overlap >= .15:
            self.merge(other, overlap)
            return True
        else:
            return False
    
    def __gt__(self, minimum_area):
        """Returns True if the area is large enough be a real photo.
        
        The purpose of this is to filter out things like specks of dust.
        """
        return self.area > minimum_area

if __name__ == '__main__':
    from PIL import Image
    from background import Background
    blank = Image.open('/home/mike/Pictures/Scans/blank.png')
    background = Background().load_from_image(blank, dpi=300)
    #print background.std_devs, background.medians
    image = Image.open('/home/mike/Pictures/Scans/1972-Saavedras/20101216153147.png')
    scan = MultiPartImage(image, background, dpi=300, deskew=True, precision=24, contrast=10)
    for photo in scan:
        photo.show()

    
