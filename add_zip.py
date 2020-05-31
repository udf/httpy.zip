#!/usr/bin/env python3
# TODO: Implement listing (-l), deleting (-d), and name override (-o)
import json
import os
import sys
import urllib.parse

host = 'http://127.0.0.1:8420'

if len(sys.argv) != 2:
    exit(1)

path = os.path.abspath(sys.argv[1])
name = os.path.split(path)[1]

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

print(urllib.parse.urljoin(host, urllib.parse.quote(name)))

with open('zip_paths.json', 'w') as f:
    json.dump(paths, f)