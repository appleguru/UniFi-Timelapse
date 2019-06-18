#!/usr/bin/env python
"""Grab a JPEG snapshot from a Ubiquiti camera at a specified interval.

Usage: python uvcsnapshot.py -c CAMERA -p PASSWORD -o OUTPUT

Required arguments:
    -c camera IP address
    -p camera password
    -o path to output directory

Optional arguments:
    -u camera username, defaults to ubnt

Example:
    python uvcsnapshot.py -x 5 -i 10 -c 192.168.0.100 -p pass1234 -o mysnaps
"""

import json

try:
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import HTTPError, Request, urlopen


class Snapshooter:
    """Class to grab snapshots from Ubiquiti cameras.

    Args:
        camera (str): IP address of the camera
        password (str): Camera password can be found in NVR settings
        username (str, optional): Username defaults to 'ubnt'
    """

    def __init__(self, camera, password, username='ubnt'):
        self.camera = camera
        self.password = password
        self.username = username

    def open(self, url, data=None, headers={}):
        """Open a URL

        Args:
            url (str): URL
            data (bytes): additional data for POST
            headers (dict): additional headers
            auth (bool): does request require login?
        """

        url = 'https://{}/api/1.2/snapshot'.format(self.camera)
        data = json.dumps({
            'username': self.username,
            'password': self.password
        }).encode('utf-8')
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = urlopen(request)
        except HTTPError as e:
            if e.code == 401:
                raise Exception('401 Invalid credentials.')
            else:
                raise
        return response

    def to_bytes(self):
        """Get a JPEG snapshot as bytes."""
        url = 'https://{}/snap.jpeg'.format(self.camera)
        response = self.open(url)
        return response.read()

    def to_file(self, path):
        """Save a JPEG snapshot to a file specified by path.

        Args:
            path (str): full path to file ending in .jpg"""
        data = self.to_bytes()
        with open(path, 'wb') as f:
            f.write(data)


if __name__ == '__main__':
    import argparse
    import os
    import time
    import datetime
    import shutil

    parser = argparse.ArgumentParser(description='Grab a snapshot from a Ubiquiti camera at a specified interval.')
    parser.add_argument('-u', '--username', nargs='?', default='ubnt', help='camera username, defaults to ubnt')
    required_named = parser.add_argument_group('required arguments')
    required_named.add_argument('-x', '--cron_interval', type=int, required=True, help='interval in minutes')
    required_named.add_argument('-i', '--interval', type=int, required=True, help='interval in seconds')
    required_named.add_argument('-c', '--camera', required=True, help='camera IP address or hostname')
    required_named.add_argument('-p', '--password', required=True, help='camera password')
    required_named.add_argument('-o', '--output', required=True, help='path to output directory')
    args = parser.parse_args()

    snapshooter = Snapshooter(
        camera=args.camera,
        password=args.password,
        username=args.username,
    )
    
    file_name = 'image.jpg'
    file_path = os.path.join(args.output, file_name)
    loopcount = int(( args.cron_interval * 60 ) / args.interval)
    for x in range(loopcount):
      timestamp = datetime.datetime.now()
      try:
          snapshooter.to_file(file_path)
          print(file_name)
      except Exception as e:
          print(('ERROR %s. %s' % (file_name, str(e))))
      
      #Copy the first image of the sequence to the archive
      if x == 0:
          archive_directory = os.path.join(args.output, timestamp.strftime('archive/%Y/%m/%d/'))
          if not os.path.exists(archive_directory):
            os.makedirs(archive_directory)

          archive_file_name = '%s.jpg' % timestamp.strftime('%Y%m%d%H%M')
          archive_file_path = os.path.join(archive_directory, archive_file_name)
          shutil.copy2(file_path, archive_file_path) #Every cron interval, copy the first image to the archive
      time.sleep(args.interval)