import optparse
import sys
from cmdutils.log import Logger

class CommandError(Exception):
    """
    Raised whenever there's some user error, to show the error to the
    user.
    """
    def __init__(self, msg, show_usage=True):
        self.msg = msg
        self.show_usage = show_usage

class OptionParser(optparse.OptionParser):

    def __init__(self,
                 usage=None,
                 option_list=None,
                 option_class=optparse.Option,
                 version=None,
                 version_package=None,
                 conflict_handler="error",
                 description=None,
                 formatter=None,
                 add_help_option=True,
                 prog=None,
                 max_args=None,
                 min_args=None,
                 use_logging=False):
        if version_package:
            if version:
                raise TypeError(
                    "You may not give both a version and version_package argument")
            import pkg_resources
            dist = pkg_resources.get_distribution(version_package)
            version='%s from %s (python %s)' % (
                dist, dist.location, '%s.%s' % (sys.version_info[:2]))
        self.max_args = max_args
        self.min_args = min_args
        self.use_logging = use_logging
        optparse.OptionParser.__init__(
            self, usage=usage, option_list=option_list, option_class=option_class,
            version=version, conflict_handler=conflict_handler,
            description=description, formatter=formatter,
            add_help_option=add_help_option, prog=prog)

    def add_verbose(self, add_quiet=True, add_log=False):
        self.add_option(
            '-v', '--verbose',
            dest="verbosity",
            help="Make the command more verbose (use multiple times to increase verbosity)",
            action="count")
        if add_quiet:
            self.add_option(
                '-q', '--quiet',
                dest="quietness",
                help="Make the command quieter (use multiple times to increase quietness)",
                action="count")
        if add_log:
            self.add_option(
                '--log',
                dest="log_file",
                metavar="FILENAME",
                help="Log verbosely to the given file")

    def get_default_values(self):
        values = optparse.OptionParser.get_default_values(self)
        values = CmdValues(values.__dict__)
        return values

    def parse_args(self, args=None, values=None):
        options, args = optparse.OptionParser.parse_args(self, args, values)
        error = None
        if self.min_args is not None and len(args) < self.min_args:
            error = 'You must provide at least %s arguments (%s given)' % (
                self.min_args, len(args))
        if self.max_args is not None and len(args) > self.max_args:
            error = 'You must provide no more than %s arguments (%s given)' % (
                self.max_args, len(args))
        if error is not None:
            logger = getattr(options, 'logger', None)
            if logger:
                logger.debug('Arguments given: %s' % args)
            self.error(error)
        return options, args

class CmdValues(optparse.Values):

    _logger = None
    
    def logger__get(self):
        if self._logger is not None:
            return self._logger
        self._logger = self._create_logger()
        return self._logger

    def logger__set(self, value):
        self._logger = logger

    def logger__del(self):
        self._logger = None

    logger = property(logger__get, logger__set, logger__del)

    def _create_logger(self):
        logger = Logger([])
        consumers = []
        verbosity = 2 # NOTIFY
        verbosity += getattr(self, 'verbosity', 0)
        verbosity -= getattr(self, 'quietness', 0)
        level = Logger.level_for_integer(verbosity)
        consumers.append((level, sys.stdout))
        if getattr(self, 'log_file', None):
            log_file = self.log_file
            log_dir = os.path.dirname(os.path.abspath(log_file))
            if not os.path.exists(log_dir):
                logger.notify('Creating directory for log file: %s' % log_dir)
                os.makedirs(log_dir)
            f = open(log_file, 'a')
            logger.consumers.append((Logger.LEVELS[-1], f))
        return logger

def run_main(main, parser, args=None):
    if args is None:
        args = sys.argv[1:]
    try:
        options, args = parser.parse_args(args)
        result = main(options, args)
    except CommandError, e:
        print str(e)
        if e.show_usage:
            parser.print_help()
        logger = getattr(options, 'logger', None)
        if logger:
            import traceback, StringIO
            out = StringIO.StringIO()
            traceback.print_exc(file=out)
            logger.debug('Failing exception:\n%s' % out.getvalue())
        result = 3
    if result:
        sys.exit(result)

def main_func(parser):
    """
    Use like::

        @main_func(parser)
        def main(options, args):
            ...
    """
    def decorator(func):
        def main(args=None):
            run_main(func, parser, args)
        return main
    return decorator

