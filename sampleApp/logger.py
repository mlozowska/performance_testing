import logging
import inspect
import os

from common import get_date_time


def basicConfig(log_file_name, log_level, log_format, log_on_console):

    console_logger = logging.getLogger('CONSOLE')
    console_logger.setLevel(logging.DEBUG)
    # create console handler and set level to info
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter(log_format)
    stream_handler.setFormatter(formatter)
    console_logger.addHandler(stream_handler)

    logger = logging.getLogger()
    logger.setLevel(log_level)

    # create error file handler and set level to error
    file_handler = logging.FileHandler(log_file_name, "w", encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if log_on_console is True:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(log_level)
        logger.addHandler(stream_handler)

    # Disabled logging for request packages
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)


def log_separator(level=None):
    logger_instance = logging.getLogger()
    if level is None:
        logger_instance.log(logging.INFO, "-" * 100)
    else:
        logger_instance.log(level, "-" * 100)


def log(level, *args):
    if len(list(args)) == 2:
        logger_name = args[0]
        message = args[1]
    elif len(list(args)) == 1:
        message = args[0]
        logger_name = ''
    else:
        raise Exception("Not enough arguments!")
    logger_instance = logging.getLogger(logger_name)

    if logger_instance.getEffectiveLevel() == logging.DEBUG:
        frame = inspect.getouterframes(inspect.currentframe())[2]
        file_name = os.path.basename(frame[1])
        trace = "%s.%s():%s" % (file_name.split(".")[0], frame[3], frame[2])
        logger_instance.log(level, "[%s] %s" % (trace, message))
    else:
        logger_instance.log(level, message)

def info(*args):
    """
    usage:
    info(logger_name, message)
    info(message)
    """
    log(logging.INFO, *args)


def debug(*args):
    """
    usage:
    debug(logger_name, message)
    debug(message)
    """
    log(logging.DEBUG, *args)


def warning(*args):
    """
    usage:
    warning(logger_name, message)
    warning(message)
    """
    log(logging.WARNING, *args)


def critical(*args):
    """
    usage:
    critical(logger_name, message)
    critical(message)
    """
    log(logging.CRITICAL, *args)


def error(*args):
    """
    usage:
    error(logger_name, message)
    error(message)
    """
    log(logging.ERROR, *args)


def fatal(*args):
    """
    usage:
    fatal(logger_name, message)
    fatal(message)
    """
    log(logging.FATAL, *args)

def console(message, marker=logging.INFO):
    info = u"[{0}] {1}".format(marker, message)
    log(marker, info)
    print (get_date_time(), info.encode("utf-8", errors='replace'))

def console_fatal(message):
    console(message=message, marker=logging.FATAL)

def console_error(message):
    console(message=message, marker=logging.ERROR)

def console_warning(message):
    console(message=message, marker=logging.WARNING)

def console_debug(message):
    console(message=message, marker=logging.DEBUG)

def logfile(message, marker=logging.INFO):
    info = u"[{0}] {1}".format(marker, message)
    log(marker, info)