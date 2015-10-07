from __future__ import print_function

import sys
import time
import logging
import argparse

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
        log.info('uploader url is {}'.format(url))

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


def make_argparser():
    parser = argparse.ArgumentParser(description='run a webcam')

    subparsers = parser.add_subparsers(help='sub-command help', dest="action")

    run_parser = subparsers.add_parser('run', help='run the webcam')
    upload_parser = subparsers.add_parser('upload', help='upload a single image')

    upload_parser.add_argument(dest='filename',
                               help='file to upload')
    upload_parser.add_argument('-u', '--url', dest="cam_url", default="127.0.0.1:8000",
                               help="url of the server")
    upload_parser.add_argument('-p', '--password', dest="password", default="beetle",
                               help="web app password")

    run_parser.add_argument('-u', '--url', dest="cam_url", default="127.0.0.1:8000",
                            help="url of the server")
    run_parser.add_argument('-r', '--rate', dest="rate", default=60.0, type=float,
                            help="delay (in seconds) between photos")
    run_parser.add_argument('-p', '--password', dest="password", default="beetle",
                            help="web app password")
    run_parser.add_argument('-q', '--quality', dest="quality", default=50, type=int,
                            help="Quality of JPEG image (1-100)")
    run_parser.add_argument('-s', '--size', dest="size", nargs=2, metavar=("WIDTH", "HEIGHT"), type=int, default=None,
                            help="Size of frame")
    run_parser.add_argument('-i', '--iso', metavar="ISO", default=None, type=int,
                            help="Camera sensitivity")

    return parser


def main():
    parser = make_argparser()
    args = parser.parse_args()
    print(args)

    def make_uploader():
        update_url = args.cam_url.rstrip('/') + '/upload/'
        if '://' not in update_url:
            update_url = "http://" + update_url
        uploader = Uploader(update_url, password=args.password)
        return uploader

    if args.action == "upload":
        uploader = make_uploader()
        uploader.upload(args.filename)

    if args.action == "run":
        uploader = make_uploader()
        next_frame = time.time()
        try:
            import picamera
        except ImportError:
            print('please insall picamera with "pip install picamera"')
            return -1
        with picamera.PiCamera() as camera:
            camera.resolution = (1024, 768)
            if args.iso is not None:
                camera.iso = args.iso
            try:

                while 1:
                    if time.time() >= next_frame:
                        next_frame += args.rate
                        try:
                            log.info('taking photo')
                            capture_time = time.time()
                            camera.capture('/tmp/frame.jpg',
                                           quality=args.quality,
                                           resize=args.size)
                            uploader.upload('/tmp/frame.jpg', timestamp=capture_time)
                        except (SystemExit, KeyboardInterrupt):
                            raise
                        except:
                            log.exception('failed to take photo')
                    else:
                        time.sleep(1)

            except (SystemExit, KeyboardInterrupt):
                return 0


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)-15s %(message)s',
                        level=logging.INFO)

    sys.exit(main() or 0)
