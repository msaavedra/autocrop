#!/usr/bin/env python2
# Copyright 2011 Michael Saavedra

"""A linux command-line utility to scan the photos placed in a scanner,
crop them, optionally de-skew them, and save them.

This should be considered a demonstration most of the capabilities of the
package, not a utility for general wide-spread use.

This depends on my cross_platform package, which is available at:
https://github.com/msaavedra/cross_platform
"""

import sys
import time
import os
import argparse
import subprocess
from StringIO import StringIO

from PIL import Image

from cross_platform import files
from autocrop.image import MultiPartImage
from autocrop.background import Background

def scan(dpi, device=None):
    args = ['scanimage']
    if device:
        args.extend(['-d', device])
    args.extend(['--resolution', str(dpi)])
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    return Image.open(StringIO(process.communicate()[0]))

def detect_scanners():
    process = subprocess.Popen(['scanimage', '-L'], stdout=subprocess.PIPE)
    scanners = []
    for line in process.stdout.readlines():
        if not line.startswith('device `'):
            continue
        line = line.strip()
        device, name = line[8:].split("' is a ", 1)
        name = '%s (%s)' % (name, device)
        scanners.append((name, device))
    return scanners

def get_default_scanner():
    if os.environ.has_key('SANE_DEFAULT_DEVICE'):
        return os.environ['SANE_DEFAULT_DEVICE']
    scanners = detect_scanners()
    if len(scanners) < 1:
        sys.stderr.write('No scanners found.\n')
        sys.exit(1)
    return scanners[0]

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
    '-f', '--filename', nargs='?', default='',
    help='Do not scan. Instead, load the image from the given file.'
    )
parser.add_argument(
    '-c', '--contrast', nargs='?', type=int, choices=range(1,11), default=5,
    help='The amount of contrast (1-10) between background and foreground. (default: 5).'
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
options.deskew = not options.disable_deskew
options.contrast = options.contrast * 2

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
    for name, device in detect_scanners():
        print name
elif options.blank:
    if options.scanner:
        devices = [options.scanner]
    else:
        devices = ['', get_default_scanner()]
    image = scan(options.resolution, options.scanner)
    background.load_from_image(image, options.resolution)
    for device in devices:
        bg_records[device] = (background.medians, background.std_devs)
    files.save_object(bg_records, BG_FILE)
else:
    date_name = time.strftime('%Y-%m-%d-%H%M%S', time.localtime(time.time()))
    letters=iter('abcdefghijklmnopqrstuvwxyz')
    if options.filename:
        image = Image.open(options.filename)
    else:
        image = scan(options.resolution, options.scanner)
    target = os.path.abspath(options.target)
    if not os.path.exists(target):
        os.makedirs(target)
    for crop in MultiPartImage(image, background,
            options.resolution, options.precision,
            options.deskew, options.contrast):
        file_name = '%s-%s.png' % (date_name, letters.next())
        full_path = os.path.join(target, file_name)
        print 'Saving %s' % full_path
        crop.save(full_path)

