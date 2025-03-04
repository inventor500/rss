#! /usr/bin/python3

from atexit import register as atexit
from logging import handlers
from queue import SimpleQueue
import logging
import sys
# if sys.platform in ("aix", "darwin", "linux", "ios", "android"):
#     # Windows et al. do not support syslog
#     import syslog

def setup_logging(name: str) -> logging.Logger:
    """Set up logging for a script."""
    logger = logging.getLogger(name)

    queue: SimpleQueue = SimpleQueue()
    async_handler = handlers.QueueHandler(queue)
    logger.addHandler(async_handler)
    formatter = logging.Formatter("%(message)s")
    async_handler.setFormatter(formatter)
    # if sys.platform in ("aix", "darwin", "linux", "ios", "android"):
    #     async_handlers: list[logging.Handler] = [handlers.SysLogHandler(facility=syslog.LOG_NEWS)]
    # else:
    #     async_handlers = []
    # async_handlers.append(logging.StreamHandler(stream=sys.stderr))
    # TODO: Syslog handler causes errors in some environments (even on UNIX)
    async_handlers = [logging.StreamHandler(stream=sys.stderr)]
    listener = handlers.QueueListener(queue, *async_handlers)
    listener.start()
    atexit(logger.info, "Finished preparing feed")
    return logger
