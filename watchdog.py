import asyncio
import logging

TIMEOUT = 10
clock = 0
logger = logging.getLogger('Watchdog')
processes = {}
last_ping = {}


def register(proc):
    processes[proc.pid] = proc
    logger.info('PID %s registered', proc.pid)


def deregister(proc):
    processes.pop(proc.pid, None)
    last_ping.pop(proc.pid, None)
    logger.info('PID %s deregistered', proc.pid)


def ping(proc):
    last_ping[proc.pid] = clock


def check(pid, proc):
    if clock - last_ping[pid] <= TIMEOUT:
        return
    logger.info('Killing PID %s', pid)
    proc.kill()
    deregister(proc)


async def watchdog():
    global clock
    logger.info('Started')
    while 1:
        for pid, proc in list(processes.items()):
            try:
                check(pid, proc)
            except Exception as e:
                logger.error('Error checking PID %s: %s', pid, e)
        await asyncio.sleep(1)
        clock += 1