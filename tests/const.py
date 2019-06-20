
import os

_file_name = __file__

while os.path.islink(_file_name):
    # Make sure we find the real script, not a symlink.
    _file_name = os.path.abspath(os.readlink(_file_name))

IMAGE_PATH = os.path.join(os.path.split(_file_name)[0], 'images')
