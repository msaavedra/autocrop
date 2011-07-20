
import os
import sys
import subprocess
from cStringIO import StringIO

from PIL import Image

if os.name == 'posix':
    
    def scan(dpi, device=None):
        args = ['scanimage']
        if device:
            args.extend(['-d', device])
        args.extend(['--resolution', str(dpi)])
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        return Image.open(StringIO(process.communicate()[0]))
    
    def detect():
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
    
    def get_default():
        if os.environ.has_key('SANE_DEFAULT_DEVICE'):
            return os.environ['SANE_DEFAULT_DEVICE']
        scanners = detect()
        if len(scanners) < 1:
            sys.stderr.write('No scanners found.\n')
            sys.exit(1)
        return scanners[0]

elif sys.platform == 'win32':
    
    def scan(dpi, scanner=None):
        pass
    
    def detect():
        pass
    
    def get_default():
        pass

if __name__ == '__main__':
    print detect()

