"""
The module will write log message to various locations in various formats
"""
import datetime
import json
import os
import traceback
from typing import Union


class LogLevel:
    """
    A class for an enumerated type for log levels
    """
    DEBUG, INFO, WARN, ERROR, FATAL = range(5)

    @staticmethod
    def get_default_log_level() -> int:
        """
        Get the system default log level
        :return: {int}
        """
        return LogLevel.INFO

    @staticmethod
    def log_level_to_text(level: int) -> Union[None, str]:
        """
        Return a string from an integer log level
        :param level: {int} Log level
        :return: {str} Log level as a string
        """
        if level == LogLevel.DEBUG:
            return 'DEBUG'
        if level == LogLevel.INFO:
            return 'INFO '
        if level == LogLevel.WARN:
            return 'WARN '
        if level == LogLevel.ERROR:
            return 'ERROR'
        if level == LogLevel.FATAL:
            return 'FATAL'
        return None

    @staticmethod
    def log_level_to_int(level_str: str) -> int:
        """
        Return an integer from a string log level
        :param level_str: {int} Log level
        :return: Log level as an integer
        """
        if level_str.strip() == 'DEBUG':
            return LogLevel.DEBUG
        if level_str.strip() == 'INFO':
            return LogLevel.INFO
        if level_str.strip() == 'WARN':
            return LogLevel.WARN
        if level_str.strip() == 'ERROR':
            return LogLevel.ERROR
        if level_str.strip() == 'FATAL':
            return LogLevel.FATAL
        return LogLevel.DEBUG


class Logger:
    """
    A class to write log entries
    """
    # set default values for these options
    APPLICATION_NAME = 'no_name'
    LOG_LEVEL = LogLevel.DEBUG
    LOG_FORMAT = None

    def __init__(self, class_name='NoClass'):
        """
        Create a logger class
        :param class_name: Logger for the specified class
        """
        self.application_name = Logger.APPLICATION_NAME
        self.class_name = class_name
        self.log_level = LogLevel.INFO
        self.out_to_file = False
        self.file = None
        if self.LOG_FORMAT == JsonFormatter.get_format_type():
            self.formatter = JsonFormatter()
        else:
            self.formatter = TextFormatter()
        self._setup_default_output()
        self._setup_default_log_level()
        self._setup_default_format()

    def _setup_default_output(self):
        """
        Use the properties to create the output target
        :return: None
        """
        output = 'stdout'

        if output == 'file':
            log_dir = os.environ['LOG_DIR']
            file = self.application_name + ".log"
            self.out_to_file = True
            self.file = open(log_dir + '/' + file, mode='a+')

        elif output in ('stdout', 'stderr'):
            self.out_to_file = False
            self.file = None

    def _setup_default_log_level(self):
        """
        Use the properties to set the log level
        :return: None
        """
        level_str = 'DEBUG'
        if 'LOG_LEVEL' in os.environ:
            level_str = os.environ['LOG_LEVEL']

        if level_str == 'DEBUG':
            self.log_level = LogLevel.DEBUG

        elif level_str == 'INFO':
            self.log_level = LogLevel.INFO

        elif level_str == 'WARN':
            self.log_level = LogLevel.WARN

        elif level_str == 'ERROR':
            self.log_level = LogLevel.ERROR

        elif level_str == 'FATAL':
            self.log_level = LogLevel.FATAL

    def _setup_default_format(self):
        """
        Use the properties to create a formatter
        :return: None
        """
        log_format = 'json'
        if 'LOG_FORMAT' in os.environ:
            log_format = os.environ['LOG_FORMAT']

        if log_format == 'json':
            self.formatter = JsonFormatter()
        elif log_format == 'text':
            self.formatter = TextFormatter()

    def set_application_name(self, application_name):
        """
        Set the application name
        :param application_name: {str} Application name
        :return: None
        """
        Logger.APPLICATION_NAME = application_name
        self.application_name = Logger.APPLICATION_NAME
        if self.out_to_file:
            log_dir = '.'
            if 'LOG_DIR' in os.environ:
                log_dir = os.environ['LOG_DIR']

            file = self.application_name + ".log"
            self.out_to_file = True
            self.file = open(log_dir + '/' + file, mode='a+')

    def debug(self, msg, error=None):
        """
        Log a message
        :param msg: {str} The message
        :param error: {Error} Error object for stacktrace
        :return: None
        """
        if self.log_level <= LogLevel.DEBUG:
            self._log_it(LogLevel.DEBUG, msg, error)

    def info(self, msg, error=None):
        """
        Log a message
        :param msg: {str} The message
        :param error: {Error} Error object for stacktrace
        :return: None
        """
        if self.log_level <= LogLevel.INFO:
            self._log_it(LogLevel.INFO, msg, error)

    def warn(self, msg, error=None):
        """
        Log a message
        :param msg: {str} The message
        :param error: {Error} Error object for stacktrace
        :return: None
        """
        if self.log_level <= LogLevel.WARN:
            self._log_it(LogLevel.WARN, msg, error)

    def error(self, msg, error=None):
        """
        Log a message
        :param msg: {str} The message
        :param error: {Error} Error object for stacktrace
        :return: None
        """
        if self.log_level <= LogLevel.ERROR:
            self._log_it(LogLevel.ERROR, msg, error)

    def fatal(self, msg, error=None, logs=None):
        """
        Log a message
        :param msg: {str} The message
        :param error: {Error} Error object for stacktrace
        :param logs: log file containing information about error
        :return: None
        """
        if self.log_level <= LogLevel.FATAL:
            self._log_it(LogLevel.FATAL, msg, error)
        # raise exception
        raise WRFCloudError(msg, logs=logs)

    def _log_it(self, level, msg, error=None):
        """
        Log a message
        :param level: {int} The log level
        :param msg: {str} The message
        :param error: {Error} Error object for stacktrace
        :return: None
        """
        entry = self.formatter.format(Logger.APPLICATION_NAME, self.class_name, level, msg, error)
        print(entry, flush=True, file=self.file)


class TextFormatter:
    """
    A class to format log entries as text
    """

    @staticmethod
    def get_format_type():
        """
        Get the format type
        :return: {str} Format type
        """
        return 'text'

    @staticmethod
    def format(application_name, class_name, level, msg, error):
        """
        Format a log message as text
        :param application_name: {str} Name of the application
        :param class_name: {str} Name of the class (if any)
        :param level: {int} Log level as an integer
        :param msg: {str} The message to log
        :param error: {Error} Error from which a stacktrace can be extracted
        :return: {str} A text log entry
        """
        time = get_timestamp()
        entry = time + ' - ' + \
            LogLevel.log_level_to_text(level) + ' - ' + \
            application_name + ' - ' + \
            class_name + ' - ' + \
            msg
        if error is not None:
            entry += '\n' + traceback_to_string(error)
        return entry


class JsonFormatter:
    """
    A class to format log entries as JSON
    """
    KEY_TIME = 'time'
    KEY_MESSAGE = 'message'
    KEY_APPLICATION = 'appName'
    KEY_CLASS = 'className'
    KEY_LEVEL = 'level'
    KEY_ERROR = 'exception'

    @staticmethod
    def get_format_type():
        """
        Get the format type
        :return: {str} Format type
        """
        return 'json'

    @staticmethod
    def format(application_name, class_name, level, msg, error):
        """
        Format a log message as JSON
        :param application_name: {str} Name of the application
        :param class_name: {str} Name of the class (if any)
        :param level: {int} Log level as an integer
        :param msg: {str} The message to log
        :param error: {Error} Error from which a stacktrace can be extracted
        :return: {str} A JSON formatted log entry
        """
        entry = {
            JsonFormatter.KEY_TIME: get_timestamp(),
            JsonFormatter.KEY_MESSAGE: msg,
            JsonFormatter.KEY_APPLICATION: application_name,
            JsonFormatter.KEY_CLASS: class_name,
            JsonFormatter.KEY_LEVEL: LogLevel.log_level_to_text(level)
        }

        if error is not None:
            entry[JsonFormatter.KEY_ERROR] = traceback_to_array(error)

        return json.dumps(entry)


def get_timestamp():
    """
    Get a current timestamp nicely formatted
    :return: {str} The timestamp as a string
    """
    time = '{0:%Y-%m-%d %H:%M:%S.000 +0000}'.format(datetime.datetime.utcnow())
    return time


def traceback_to_string(error):
    """
    Convert a traceback to a string
    :param error: {Error} The error with a traceback
    :return: {str} The traceback as a string
    """
    tb_lines = traceback.format_exception(None, error, error.__traceback__)
    full_traceback = ''.join(tb_lines)
    return full_traceback


def traceback_to_array(error):
    """
    Convert a traceback to a string
    :param error: {Error} The error with a traceback
    :return: {str} The traceback as a string
    """
    return traceback.format_exception(None, error, error.__traceback__)


class WRFCloudError(Exception):
    def __init__(self, message, logs=None):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        # store error message to send to UI
        self.message = message
        # capture any error logs
        self.logs = logs
