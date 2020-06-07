# httpy.zip

## What is this?
A HTTP server that serves zip files of directories.

## Usage
1. Copy `config_example.py` to `config.py` and open it in a text editor.
1. Edit the `route_dirs` variable to point to your directory full of totally legal files

    Let's say you have a directory structure like this:
    ```
    home/rzr/files
    ├── Memes
    │   └── pepe
    └── pr0n
    ```

    And you set `route_dirs` like this:

    ```python
    route_dirs = {
        '/arr/': '/home/rzr/files'
    }
    ```

    You can download a zip of your top level subdirectories:  
    http://127.0.0.1:8420/arr/Memes.zip (works)  
    http://127.0.0.1:8420/arr/pr0n.zip (works)

    but non-top level subdirectories are not allowed:  
    http://127.0.0.1:8420/arr/Memes/pepe.zip (404)

1. If you want to restrict access to only certain directories/give custom names to the files, point `route_dirs` to an empty directory and link your directories inside there.

## Further setup
You probably want to put this behind a reverse proxy instead of hosting it bare. A sample nginx proxy.d config has been provided to get you started.

## FAQ
### HTTPS? Authentication?
Use a reverse proxy, see the sample nginx config file.

### Why are you running the zip command instead of doing the zipping in Python?
I don't see any advantages to using only Python. Convince me and maybe I'll switch to pure Python.
