# -*- coding: utf-8 -*-

try:
    import logHandler
    log = logHandler.log
except Exception:
    log = None


def logDebug(message):
    if log is None:
        return

    try:
        log.debugWarning(message, exc_info=True)
    except Exception:
        pass