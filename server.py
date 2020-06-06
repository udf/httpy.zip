import asyncio
import json
import logging
import os
import shlex
from aiohttp import web


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
dir_paths = {}


def reload_list():
    global dir_paths
    with open('zip_paths.json') as f:
        dir_paths = json.load(f)
    missing = []
    for zip_name, path in dir_paths.items():
        if not os.path.exists(path):
            missing.append('{}: {}'.format(zip_name, path))
    if missing:
        missing.insert(0, 'The following paths were not found:')
    return missing


async def handle_reload_list(request):
    missing = reload_list()
    return web.Response(text='\n'.join(missing))


async def log_stream(stream, logger):
    while not stream.at_eof():
        line = await stream.read(1024)
        logger.info(line.decode().strip())


async def handle_zip(request):
    name = request.match_info.get('name')
    if name not in dir_paths:
        return web.HTTPForbidden()
    path = dir_paths[name]
    if not os.path.exists(path):
        return web.HTTPGone()

    response = web.StreamResponse(status=200)
    response.content_type = 'application/octet-stream'
    await response.prepare(request)

    chunk_size = 1024 * 1024
    logger.info('Sending "%s" -> "%s"', path, name)
    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            'zip', '-r', '-0', '-', '.',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=chunk_size,
            cwd=path
        )
        asyncio.ensure_future(log_stream(
            proc.stderr,
            logging.getLogger('zip ({})'.format(proc.pid))
        ))

        while not proc.stdout.at_eof():
            chunk = await proc.stdout.read(chunk_size)
            if chunk:
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
        if proc:
            proc.kill()

    return response


app = web.Application()
app.add_routes([
    web.get('/{name}', handle_zip),
    web.get('/admin/reload', handle_reload_list)
])

if __name__ == '__main__':
    print('\n'.join(reload_list()))
    web.run_app(
        app,
        host='127.0.0.1',
        port=8420
    )