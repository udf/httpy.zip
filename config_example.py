# path used by add_zip.py when printing the url
http_path = 'https://your.domain/zip/'

# port used by the server and add_zip.py for sending the reload command
port = 8420

# size of zip stdout buffer in bytes
chunk_size = 1024 * 1024

# dict of {'web route': 'disk path'}
# Every top level subdirectory of the path will be available at the web route,
# but the root path will not be accessible
route_dirs = {
    '/web/route': '/path/to/files'
}