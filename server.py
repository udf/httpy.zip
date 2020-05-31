import asyncio
import json
import logging
import os
import shlex
from aiohttp import web

import watchdog


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
    err = await stream.read()
    if not err:
        return
    for line in err.decode().split('\n'):
        line = line.strip()
        if not line:
            continue
        logger.info(line)


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
    proc = await asyncio.create_subprocess_exec(
        'zip', '-r', '-0', '-', '.',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        limit=chunk_size,
        cwd=path
    )
    ziplogger = logging.getLogger('zip ({})'.format(proc.pid))
    watchdog.register(proc)

    while not proc.stdout.at_eof():
        await log_stream(proc.stderr, ziplogger)

        chunk = await proc.stdout.read(chunk_size)
        if chunk:
            watchdog.ping(proc)
            await response.write(chunk)

    await log_stream(proc.stderr, ziplogger)

    watchdog.deregister(proc)
    return_code = await asyncio.wait_for(proc.wait(), timeout=1)
    if return_code != 0:
        logger.warning(
            'zip PID %s terminated with code %s',
            proc.pid,
            proc.returncode
        )
        return web.HTTPInternalServerError()

    return response


async def main(app):
    asyncio.ensure_future(watchdog.watchdog())


app = web.Application()
app.add_routes([
    web.get('/{name}', handle_zip),
    web.get('/admin/reload', handle_reload_list)
])
app.on_startup.append(main)

if __name__ == '__main__':
    print('\n'.join(reload_list()))
    web.run_app(
        app,
        host='127.0.0.1',
        port=8420
    )