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
from simple_config import Config
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
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    output = process.communicate()[0]
    if process.returncode > 0:
        sys.exit(1)
        
    image = Image.open(BytesIO(output))
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


def parse_commandline_options(defaults):
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
        default=defaults.resolution,
        help=(
            'The resolution, in dots per inch, to use while '
            'scanning (default: 300).'
            )
        )
    parser.add_argument(
        '-p', '--precision',
        nargs='?',
        type=int,
        default=defaults.precision,
        help=(
            'The precision to use while cropping. Higher is better '
            'but slower (default: 50).'
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
        nargs='*',
        default='',
        help='Do not scan. Instead, load the image from the given file(s).'
        )
    parser.add_argument(
        '-c', '--contrast',
        nargs='?',
        type=int,
        choices=list(range(1, 11)),
        default=defaults.contrast,
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
        '-k', '--shrink',
        nargs='?',
        type=int,
        default=defaults.shrink,
        help=(
            'Number of pixels to shrink the area to be cropped. Avoid a possible small '
            'white border at the cost of a slightly smaller image. Only relevant if '
            'the image is deskewed (default: 3)'
            )
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
    options.contrast = options.contrast * 3
    return options


def list_all_scanners():
    # List all scanners.
    for name, device in detect_scanners():
        print(name)


def get_config_params():
    default_params = {
        "resolution": 300,
        "shrink": 0,
        "contrast": 5,
        "precision": 50
    }
    return Config(os.path.join(AUTOCROP_DIR, 'config.json'), defaults=default_params)


def scan_and_save_background_data(options, background, bg_records, bg_file):
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


def autocrop_file(options, image, background):
    # Autocrop a file.
    date_name = time.strftime(
        '%Y-%m-%d-%H%M%S',
        time.localtime(time.time())
    )
    letters = iter('abcdefghijklmnopqrstuvwxyz')
    target = os.path.abspath(options.target)
    if not os.path.exists(target):
        os.makedirs(target)

    multipart_image = MultiPartImage(
        image,
        background,
        options.resolution,
        options.precision,
        options.deskew,
        options.contrast,
        options.shrink
    )
    for crop in multipart_image:
        file_name = '%s-%s.png' % (date_name, next(letters))
        full_path = os.path.join(target, file_name)
        print('Saving %s' % full_path)
        crop.save(full_path)

    full_path_original_image = os.path.join(target, 'tmp-full-scan.jpg')
    multipart_image.image.save(full_path_original_image, quality=90)


def main():
    options = parse_commandline_options(get_config_params())
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
        background = Background(*bg_records[device_name])
    else:
        background = Background()
    
    if options.list:
        list_all_scanners()
    
    elif options.blank:
        scan_and_save_background_data(options, background, bg_records, bg_file)
    
    else:
        if options.filename:
            for filename in options.filename:
                print(f'autocrop {filename}')
                image = Image.open(filename)
                autocrop_file(options, image, background)
        else:
            image = scan(options.resolution, options.scanner)
            autocrop_file(options, image, background)


if __name__ == '__main__':
    main()
