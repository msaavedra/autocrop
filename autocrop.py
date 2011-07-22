#!/usr/bin/env python2

import sys
import time
import os
import argparse

from PIL import Image

from cross_platform import files
from autocrop.image import MultiPartImage
from autocrop.background import Background
from autocrop import scanner

parser = argparse.ArgumentParser(
    description='A utility to crop multiple photos out of a scanned sheet.'
    )
parser.add_argument(
    '-b', '--blank', action='store_true',
    help="Make a blank scan (with no photos in the scanner) for calibration."
    )
parser.add_argument(
    '-l', '--list', action='store_true',
    help="List available scanning devices."
    )
parser.add_argument(
    '-r', '--resolution', nargs='?', type=int, default=300,
    help='The resolution, in dots per inch, to use while scanning (default: 300).'
    )
parser.add_argument(
    '-p', '--precision', nargs='?', type=int, default=24,
    help='The precision to use while cropping. Higher is better but slower (default: 20).'
    )
parser.add_argument(
    '-s', '--scanner', nargs='?', default='',
    help='The scanner to use. If not specified, the system default is used.'
    )
parser.add_argument(
    '-c', '--contrast', nargs='?', default='medium',
    help='The amount of contrast (either high, medium, or low) between background and foreground. (default: medium).'
    )
parser.add_argument(
    '-d', '--disable-deskew', action='store_true',
    help='Do not auto-correct the rotation of the photos after cropping.'
    )
parser.add_argument(
    'target', nargs='?', default=os.getcwd(),
    help='The destination directory of the cropped photos (default: the current working directory).'
    )
options = parser.parse_args()

BG_FILE = os.path.join(files.APP_CONF_DIR, 'autocrop', 'backgrounds')
if os.path.exists(BG_FILE):
    bg_records = files.load_object(BG_FILE)
else:
    bg_records = {}
if bg_records.has_key(options.scanner):
    background = Background(*bg_records[options.scanner])
else:
    background = Background()

if options.list:
    for name, device in scanner.detect():
        print name
elif options.blank:
    if options.scanner:
        devices = [options.scanner]
    else:
        devices = ['', scanner.get_default()]
    image = scanner.scan(options.resolution, options.scanner)
    background.load_from_image(image, options.resolution)
    for device in devices:
        bg_records[device] = (background.medians, background.std_devs)
    files.save_object(bg_records, BG_FILE)
else:
    letters='abcdefjhijklmnopqrstuvwxyz'
    date_name = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
    count = 0
    image = scanner.scan(options.resolution, options.scanner)
    target = os.path.abspath(options.target)
    if not os.path.exists(target):
        os.makedirs(target)
    for crop in MultiPartImage(image, background,
            options.resolution, options.precision, not options.disable_deskew):
        file_name = '%s%s.png' % (date_name, letters[count])
        full_path = os.path.join(target, file_name)
        crop.save(full_path)
        count += 1
    print 'Found %d photos.' % count

