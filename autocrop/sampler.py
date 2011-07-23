# Copyright 2011 Michael Saavedra

class ReachedEdge(StopIteration): pass

class PixelSampler(object):
    """An iterator to collect regularly spaced pixel samples from an image.
    
    It also has methods to get samples adjacent to a particular point.
    """
    def __init__(self, image, dpi, precision=16):
        self.image = image
        self.width, self.height = image.size
        self.data = image.load()
        self.dpi = dpi
        if precision > dpi:
            # A sampler step smaller than one pixel is impossible
            self.precision = dpi
        elif precision == 0:
            # We want to avoid division-by-zero errors.
            self.precision = 1
        else:
            self.precision = precision
        
        self.step = int(self.dpi / self.precision)
    
    def __iter__(self):
        for x, y, r, g, b in self.run(self.down, self.step, self.step):
            for result in self.run(self.right, x, y, self.step):
                yield result
    
    def run(self, direction, x, y, distance=0, maximum=0):
        if distance == 0:
            distance = self.step
        count = 0
        red, green, blue = self.data[x, y][:3]
        yield x, y, red, green, blue
        while True:
            result = direction(x, y, distance)
            yield result
            if maximum:
                count += 1
                if count == maximum:
                    break
            x, y = result[:2]
    
    def up(self, x, y, distance=0):
        if distance == 0:
            distance = self.step
        if y == distance:
            raise ReachedEdge(x, y)
        y -= distance
        if y < distance:
            y = distance
        red, green, blue = self.data[x, y][:3]
        return (x, y, red, green, blue)
    
    def down(self, x, y, distance=0):
        if distance == 0:
            distance = self.step
        max_y = self.height - distance
        if y == max_y:
            raise ReachedEdge(x, y)
        y += distance
        if y > max_y:
            y = max_y
        red, green, blue = self.data[x, y][:3]
        return (x, y, red, green, blue)
    
    def left(self, x, y, distance=0):
        if distance == 0:
            distance = self.step
        if x == distance:
            raise ReachedEdge(x, y)
        x -= distance
        if x < distance:
            x = distance
        red, green, blue = self.data[x, y][:3]
        return (x, y, red, green, blue)
    
    def right(self, x, y, distance=0):
        if distance == 0:
            distance = self.step
        max_x = self.width - distance
        if x == max_x:
            raise ReachedEdge(x, y)
        x += distance
        if x > max_x:
            x = max_x
        red, green, blue = self.data[x, y][:3]
        return (x, y, red, green, blue)
    
    def around(self, x, y, distance=0):
        for f in (self.up, self.right, self.down, self.left):
            try:
                yield f(x, y, distance)
            except ReachedEdge:
                continue


