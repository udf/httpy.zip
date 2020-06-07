import asyncio
import logging
import os
from pathlib import Path
import urllib.parse
from functools import partial
from aiohttp import web

import config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


async def log_stream(stream, logger):
    while not stream.at_eof():
        line = await stream.read(1024)
        if not line:
            continue
        logger.info(line.decode().strip())


async def handle_zip(request, root):
    subdir = request.match_info.get('subdir')

    root = Path(root)
    path = os.path.abspath(Path(root) / subdir)
    # Only allow subdirectories of root
    try:
        subdir = Path(path).relative_to(root)
    except ValueError:
        return web.HTTPForbidden()
    # Only allow a single level of traversal
    if len(subdir.parents) != 1:
        return web.HTTPForbidden()
    # Only allow directories
    if not os.path.isdir(path):
        return web.HTTPNotFound()

    response = web.StreamResponse(status=200)
    response.content_type = 'application/octet-stream'
    await response.prepare(request)

    logger.info('Sending "%s"', path)
    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            'zip', '-r', '-0', '-', '.',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=config.chunk_size,
            cwd=path
        )
        asyncio.ensure_future(log_stream(
            proc.stderr,
            logging.getLogger('zip ({})'.format(proc.pid))
        ))

        while not proc.stdout.at_eof():
            chunk = await proc.stdout.read(config.chunk_size)
            await response.write(chunk)

        return_code = await asyncio.wait_for(proc.wait(), timeout=1)
        if return_code != 0:
            logger.warning(
                'zip PID %s terminated with code %s',
                proc.pid,
                proc.returncode
            )
            return web.HTTPInternalServerError()
    finally:
        try:
            if proc:
                proc.kill()
        except ProcessLookupError:
            pass

    return response


app = web.Application()
for route, root in config.route_dirs.items():
    root = os.path.abspath(root)
    path = urllib.parse.urljoin(route, '{subdir}.zip')
    logger.info('Route "%s" -> "%s"', path, root)
    app.router.add_get(path, partial(handle_zip, root=root))

if __name__ == '__main__':
    web.run_app(
        app,
        host='127.0.0.1',
        port=config.port
    )