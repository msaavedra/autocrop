#!/usr/bin/env python3
# Copyright 2011 Michael Saavedra

"""A linux command-line utility to scan the photos placed in a scanner,
crop them, optionally de-skew them, and save them.

This should be considered a demonstration most of the capabilities of the
package, not a utility for general wide-spread use.
"""

import argparse
import errno
from io import BytesIO
import json
import os
import subprocess
import sys
import tempfile
import time

from PIL import Image

from autocrop.image import MultiPartImage
from autocrop.background import Background


if os.name == 'posix':
    APP_CONF_DIR = os.environ.get(
        'XDG_DATA_HOME',
        os.path.join(os.environ['HOME'], '.config')
        )
else:
    sys.stderr.write('Not a supported platform.\n')
    sys.exit(1)

AUTOCROP_DIR = os.path.join(APP_CONF_DIR, 'autocrop')
os.makedirs(AUTOCROP_DIR, mode=0o700, exist_ok=True)


def scan(dpi, device=None):
    args = ['scanimage']
    if device:
        if isinstance(device, (list, tuple)):
            device = device[1]
        args.extend(['-d', device])
    args.extend(['--resolution', str(dpi), '--mode', 'Color'])
    print(args)
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    output = process.communicate()[0]
    if process.returncode > 0:
        sys.exit(1)
        
    image = Image.open(BytesIO(output))
    print(f'Scanned image attributes: {image.mode} {image.size}')
    return image

def detect_scanners():
    process = subprocess.Popen(['scanimage', '-L'], stdout=subprocess.PIPE)
    scanners = []
    for line in process.stdout.readlines():
        line = line.decode('utf-8')
        if not line.startswith('device `'):
            continue
        line = line.strip()
        device, name = line[8:].split("' is a ", 1)
        name = '%s (%s)' % (name, device)
        scanners.append((name, device))
    return scanners


def get_default_scanner():
    if 'SANE_DEFAULT_DEVICE' in os.environ:
        return os.environ['SANE_DEFAULT_DEVICE']
    scanners = detect_scanners()
    if not scanners:
        sys.stderr.write('No scanners found.\n')
        sys.exit(1)
    return scanners[0]


def get_scanner_base_name(device):
    if isinstance(device, (list, tuple)):
        device = device[0]
    
    name = device.partition('(')[0].strip()
    print(name)
    return name


def parse_commandline_options():
    parser = argparse.ArgumentParser(
        description='A utility to crop multiple photos out of a scanned image.'
        )
    parser.add_argument(
        '-b', '--blank',
        action='store_true',
        help=(
            'Make a blank scan (with no photos in the scanner) '
            'for calibration.'
            )
        )
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help="List available scanning devices."
        )
    parser.add_argument(
        '-r', '--resolution',
        nargs='?',
        type=int,
        default=300,
        help=(
            'The resolution, in dots per inch, to use while '
            'scanning (default: 300).'
            )
        )
    parser.add_argument(
        '-p', '--precision',
        nargs='?',
        type=int,
        default=24,
        help=(
            'The precision to use while cropping. Higher is better '
            'but slower (default: 24).'
            )
        )
    parser.add_argument(
        '-s', '--scanner',
        nargs='?',
        default='',
        help=(
            'The scanner to use. If not specified, '
            'the system default is used.'
            )
        )
    parser.add_argument(
        '-f', '--filename',
        nargs='?',
        default='',
        help='Do not scan. Instead, load the image from the given file.'
        )
    parser.add_argument(
        '-c', '--contrast',
        nargs='?',
        type=int,
        choices=list(range(1, 11)),
        default=5,
        help=(
            'The amount of contrast (1-10) between background '
            'and foreground. (default: 5).'
            )
        )
    parser.add_argument(
        '-d', '--disable-deskew',
        action='store_true',
        help='Do not auto-correct the rotation of the photos after cropping.'
        )
    parser.add_argument(
        'target',
        nargs='?',
        default=os.getcwd(),
        help=(
            'The destination directory of the cropped photos '
            '(default: the current working directory).'
            )
        )
    options = parser.parse_args()
    options.deskew = not options.disable_deskew
    options.contrast = options.contrast * 2
    return options


def main(options):
    bg_file = os.path.join(AUTOCROP_DIR, 'backgrounds.json')
    try:
        with open(bg_file, 'r') as f:
            bg_records = json.load(f)
    except OSError as e:
        if e.errno == errno.ENOENT:
            bg_records = {}
        else:
            raise
    
    device_name = get_scanner_base_name(options.scanner)
    if device_name in bg_records:
        print('loading sample background data')
        background = Background(*bg_records[device_name])
    else:
        background = Background()
    
    if options.list:
        # List all scanners.
        for name, device in detect_scanners():
            print(name)
    
    elif options.blank:
        # Scan and save background data.
        if options.scanner:
            devices = [options.scanner]
        else:
            devices = ['', get_default_scanner()]
        image = scan(options.resolution, options.scanner)
        background.load_from_image(image, options.resolution)
        for device in devices:
            name = get_scanner_base_name(device)
            bg_records[name] = (background.medians, background.std_devs)
        print(bg_records)
        temp_bg_file = tempfile.NamedTemporaryFile(
            mode='w',
            dir=AUTOCROP_DIR,
            delete=False
            )
        temp_bg_file_name = temp_bg_file.name
        try:
            json.dump(bg_records, temp_bg_file)
        except:
            os.remove(temp_bg_file_name)
            raise
        finally:
            temp_bg_file.close()
        
        os.rename(temp_bg_file_name, bg_file)
        
    
    else:
        # Autocrop a file.
        date_name = time.strftime(
            '%Y-%m-%d-%H%M%S',
            time.localtime(time.time())
            )
        letters = iter('abcdefghijklmnopqrstuvwxyz')
        if options.filename:
            image = Image.open(options.filename)
        else:
            image = scan(options.resolution, options.scanner)
        target = os.path.abspath(options.target)
        if not os.path.exists(target):
            os.makedirs(target)
        multipart_image = MultiPartImage(
            image,
            background,
            options.resolution,
            options.precision,
            options.deskew,
            options.contrast
            )
        for crop in multipart_image:
            file_name = '%s-%s.png' % (date_name, next(letters))
            full_path = os.path.join(target, file_name)
            print('Saving %s' % full_path)
            crop.save(full_path)


if __name__ == '__main__':
    main(parse_commandline_options())
