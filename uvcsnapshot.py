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
    python uvcsnapshot.py -c 192.168.0.100 -p pass1234 -o mysnaps
"""

import json

try:
    from http.cookiejar import CookieJar
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen
except ImportError:
    from cookielib import CookieJar
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
        self.jar = CookieJar()
        self.login()

    def open(self, url, data=None, headers={}, auth=False):
        """Open a URL and persist cookies in a CookieJar.

        Args:
            url (str): URL
            data (bytes): additional data for POST
            headers (dict): additional headers
            auth (bool): does request require login?
        """
        if auth:
            # If auth is required, check if we have a session cookie.
            has_session = False
            for cookie in self.jar:
                if cookie.name == 'authId':
                    has_session = True
                    break
            if not has_session:
                self.login()
        request = Request(url, data=data, headers=headers)
        self.jar.add_cookie_header(request)
        try:
            response = urlopen(request)
        except HTTPError as e:
            if auth and e.code == 401:
                # Session cookie is invalid. Login and try again.
                self.login()
                response = urlopen(request)
            else:
                raise
        self.jar.extract_cookies(response, request)
        return response

    def login(self):
        """Login to the camera and create a session."""
        url = 'https://{}/api/1.1/login'.format(self.camera)
        data = json.dumps({
            'username': self.username,
            'password': self.password
        }).encode('utf-8')
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = self.open(url, data, headers)
        except HTTPError as e:
            if e.code == 401:
                raise Exception('401 Invalid credentials.')
            else:
                raise

    def to_bytes(self):
        """Get a JPEG snapshot as bytes."""
        url = 'https://{}/snap.jpeg'.format(self.camera)
        response = self.open(url, auth=True)
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

    parser = argparse.ArgumentParser(description='Grab a snapshot from a Ubiquiti camera')
    parser.add_argument('-u', '--username', nargs='?', default='ubnt', help='camera username, defaults to ubnt')
    required_named = parser.add_argument_group('required arguments')
    required_named.add_argument('-c', '--camera', required=True, help='camera IP address or hostname')
    required_named.add_argument('-p', '--password', required=True, help='camera password')
    required_named.add_argument('-o', '--output', required=True, help='path to output directory')
    args = parser.parse_args()

    snapshooter = Snapshooter(
        camera=args.camera,
        password=args.password,
        username=args.username,
    )
    
    timestamp = datetime.datetime.now()
    save_directory = os.path.join(args.output, timestamp.strftime('%Y/%m/%d/'))
    if not os.path.exists(save_directory):
      os.makedirs(save_directory)
    
    file_name = '%s.jpg' % timestamp.strftime('%Y%m%d%H%M%S')
    file_path = os.path.join(save_directory, file_name)
    try:
        snapshooter.to_file(file_path)
        print(file_name)
    except Exception as e:
        print(('ERROR %s. %s' % (file_name, str(e))))
