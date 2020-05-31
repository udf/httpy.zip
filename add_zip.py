#!/usr/bin/env python3
# TODO: Implement listing (-l), deleting (-d), and name override (-o)
import json
import os
import sys
import urllib.parse
import urllib.request

from config import http_path, port

if len(sys.argv) != 2:
    exit(1)

path = os.path.abspath(sys.argv[1])
name = os.path.split(path)[1] + '.zip'

if not os.path.exists(path):
    print('Not found:', path)
    exit(2)

try:
    with open('zip_paths.json') as f:
        paths = json.load(f)
except FileNotFoundError:
    paths = {}

if name in paths and paths[name] != path:
    print('Name already exists as', paths[name])
    exit(3)

paths[name] = path

print(urllib.parse.urljoin(http_path, urllib.parse.quote(name)))

with open('zip_paths.json', 'w') as f:
    json.dump(paths, f)

print('Sending reload command...')
host = 'http://127.0.0.1:{}'.format(port)
url = urllib.parse.urljoin(host, '/admin/reload')
with urllib.request.urlopen(url) as response:
    print(response.read().decode())