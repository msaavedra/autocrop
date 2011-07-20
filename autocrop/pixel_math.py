"""Statistical and trigonometric functions to aid in image processing.
"""
from math import atan2, cos, radians, degrees

def get_median(seq):
    seq.sort()
    length = len(seq)
    
    if length == 0:
        return 0
    
    i = length / 2
    if length % 2 == 1:
        return float(seq[i])
    else:
        return (seq[i-1] + seq[i]) / float(2)

def get_standard_deviation(seq):
    length = float(len(seq))
    mean = sum(seq) / length
    return (sum([(n - mean)**2 for n in seq]) / length)**.5

def get_angle(rise, run):
    return degrees(atan2(rise, run))

def get_adjacent(angle, hypotenuse):
    return int(cos(radians(angle)) * hypotenuse)

