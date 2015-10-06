from __future__ import print_function
from __future__ import unicode_literals

import sys
import time
import logging

try:
    import requests
except ImportError:
    sys.stderr.write('please install requests library with "pip install requests"')
    sys.exit(-1)


log = logging.getLogger('beetlecam.upload')


class Uploader(object):
    def __init__(self, url, password='beetle'):
        self.url = url
        self.password = password

    def upload(self, filename, timestamp=None):
        if timestamp is None:
            timestamp = time.time()

        form_data = {
            "taken": timestamp,
            "password": self.password
        }
        try:
            files = {
                "image": open(filename, 'rb')
            }
        except IOError:
            log.exception('failed to read image file')
            return False
        try:
            req = requests.post(self.url, form_data, files=files)
        except:
            log.exception('failed to send frame')
            return False

        msg = req.headers.get('beetlecam_upload', None)
        if msg is not None:
            log.info(msg)

        if req.status_code != 200:
            log.warning('upload failed')
            return False

        return True


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)-15s %(message)s',
                        level=logging.INFO)

    uploader = Uploader("http://127.0.0.1:8000/upload/")
    uploader.upload(sys.argv[1])
