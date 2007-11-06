import logging
import sys
import os

class Logger(object):

    """
    Logging object for use in command-line script.  Allows ranges of
    levels, to avoid some redundancy of displayed information.
    """

    VERBOSE_DEBUG = logging.DEBUG-10
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    NOTIFY = (logging.INFO+logging.WARN)/2
    WARN = WARNING = logging.WARN
    ERROR = logging.ERROR
    FATAL = logging.FATAL

    LEVELS = [VERBOSE_DEBUG, DEBUG, INFO, NOTIFY, WARN, ERROR, FATAL]

    def __init__(self, consumers, send_to_logging=False,
                 logging_name=None):
        self.consumers = consumers
        self.indent = 0
        self.level_adjust = 0
        self.in_progress = None
        self.in_progress_hanging = False
        self.send_to_logging = send_to_logging
        if isinstance(logging_name, basestring):
            self.logger = logging.getLogger(logging_name)
        elif not logging_name:
            if send_to_logging:
                self.logger = logging.getLogger('')
            else:
                self.logger = None
        else:
            self.logger = logging_name
        self.section = None
        self._added_consumers = False
        

    def set_section(self, section):
        self.section = section
        self._section_logs = []
        self._section_color_logs = []
        if not self._added_consumers:
            self.consumers.append((self.VERBOSE_DEBUG, self._append_section))
            self.consumers.append((self.VERBOSE_DEBUG, self._append_section_color))
            self._added_consumers = True

    def remove_section(self):
        self.section = None
        self._section_logs = self._section_color_logs = None
        ## FIXME: should remove consumers

    def section_text(self, color=None):
        if not self.section:
            return
        if color is None:
            color = self.supports_color(sys.stdout)
        if color:
            logs = self._section_color_logs
        else:
            logs = self._section_logs
        return '\n'.join(logs)

    def _append_section(self, msg):
        if self.section:
            self._section_logs.append(msg)

    def _append_section_color(self, msg):
        if self.section:
            self._section_color_logs.append(msg)
    _append_section_color.color = True

    def debug(self, msg, *args, **kw):
        self.log(self.DEBUG, msg, *args, **kw)
    def info(self, msg, *args, **kw):
        self.log(self.INFO, msg, *args, **kw)
    def notify(self, msg, *args, **kw):
        self.log(self.NOTIFY, msg, *args, **kw)
    def warn(self, msg, *args, **kw):
        self.log(self.WARN, msg, *args, **kw)
    def error(self, msg, *args, **kw):
        self.log(self.WARN, msg, *args, **kw)
    def fatal(self, msg, *args, **kw):
        self.log(self.FATAL, msg, *args, **kw)
    def log(self, level, msg, *args, **kw):
        if 'color' in kw:
            color = kw.pop('color')
        else:
            color = None
        level = self.adjusted_level(level)
        if args:
            if kw:
                raise TypeError(
                    "You may give positional or keyword arguments, not both")
        args = args or kw
        rendered = None
        for consumer_level, consumer in self.consumers:
            if self.level_matches(level, consumer_level):
                if (self.in_progress_hanging
                    and consumer in (sys.stdout, sys.stderr)):
                    self.in_progress_hanging = False
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                if rendered is None:
                    if args:
                        rendered = msg % args
                    else:
                        rendered = msg
                    rendered = self.indented(rendered)
                cons_rendered = rendered
                if color and self.supports_color(consumer):
                    cons_rendered = self.colorize(cons_rendered, color)
                if hasattr(consumer, 'write'):
                    consumer.write(cons_rendered+'\n')
                else:
                    consumer(cons_rendered)
        if self.send_to_logging:
            self.logger.log(level, msg, *args, **kw)

    def adjusted_level(self, level):
        if not self.level_adjust:
            return level
        if isinstance(level, tuple):
            return tuple(map(self.adjust_level, level))
        try:
            index = self.LEVELS.index(level)
        except ValueError:
            return level
        index += self.level_adjust
        if index >= len(self.LEVELS):
            return self.LEVELS[-1]
        elif index < 0:
            return self.LEVELS[0]
        else:
            return self.LEVELS[index]

    def start_progress(self, msg):
        assert not self.in_progress, (
            "Tried to start_progress(%r) while in_progress %r"
            % (msg, self.in_progress))
        if self.level_matches(self.NOTIFY, self._stdout_level()):
            sys.stdout.write(' '*self.indent+msg)
            sys.stdout.flush()
            self.in_progress_hanging = True
        else:
            self.in_progress_hanging = False
        self.in_progress = msg

    def end_progress(self, msg='done.'):
        assert self.in_progress, (
            "Tried to end_progress without start_progress")
        if self.stdout_level_matches(self.NOTIFY):
            if not self.in_progress_hanging:
                # Some message has been printed out since start_progress
                sys.stdout.write(' '*self.indent + '...' + self.in_progress + msg + '\n')
                sys.stdout.flush()
            else:
                sys.stdout.write(msg + '\n')
                sys.stdout.flush()
        self.in_progress = None
        self.in_progress_hanging = False

    def show_progress(self):
        """If we are in a progress scope, and no log messages have been
        shown, write out another '.'"""
        if self.in_progress_hanging:
            sys.stdout.write('.')
            sys.stdout.flush()

    def stdout_level_matches(self, level):
        """Returns true if a message at this level will go to stdout"""
        return self.level_matches(level, self._stdout_level())

    def _stdout_level(self):
        """Returns the level that stdout runs at"""
        for level, consumer in self.consumers:
            if consumer is sys.stdout:
                return level
        return self.FATAL

    def level_matches(self, level, consumer_level):
        """
        >>> l = Logger()
        >>> l.level_matches(3, 4)
        False
        >>> l.level_matches(3, 2)
        True
        >>> l.level_matches(slice(None, 3), 3)
        False
        >>> l.level_matches(slice(None, 3), 2)
        True
        >>> l.level_matches(slice(1, 3), 1)
        True
        >>> l.level_matches(slice(2, 3), 1)
        False
        """
        if isinstance(level, slice):
            start, stop = level.start, level.stop
            if start is not None and start > consumer_level:
                return False
            if stop is not None or stop <= consumer_level:
                return False
            return True
        else:
            return level >= consumer_level

    #@classmethod
    def level_for_integer(cls, level):
        levels = cls.LEVELS
        if level < 0:
            return levels[0]
        if level >= len(levels):
            return levels[-1]
        return levels[level]

    level_for_integer = classmethod(level_for_integer)

    def supports_color(self, consumer):
        if getattr(consumer, 'color', False):
            return True
        try:
            isatty = getattr(consumer, 'isatty')()
        except AttributeError:
            return False
        if not isatty:
            return False
        ## FIXME: this is a lame test
        return os.environ.get('LSCOLORS') or os.environ.get('LS_COLORS')

    def colorize(self, msg, color):
        msg = string_to_ansi(color) + msg + string_to_ansi('reset')
        return msg

    def indented(self, text):
        if not self.indent:
            return text
        lines = text.splitlines(True)
        return ''.join([(' '*self.indent)+line for line in lines])

ansi_codes = dict(
    reset=0,
    bold=1,
    italic=3,
    underline=4,
    inverse=7,
    strike=9,
    bold_off=22,
    italic_off=23,
    underline_off=24,
    strike_off=29,
    black=30,
    red=31,
    green=32,
    yellow=33,
    blue=34,
    magenta=35,
    cyan=36,
    white=37,
    default_color=39,
    black_bg=40,
    red_bg=41,
    green_bg=42,
    yellow_bg=43,
    blue_bg=44,
    magenta_bg=45,
    cyan_bg=46,
    white_bg=47,
    default_bg=49,
    )

def string_to_ansi(string):
    parts = string.split()
    codes = []
    for part in parts:
        if part not in ansi_codes:
            raise ValueError(
                "Bad code: %r" % part)
        codes.append(ansi_codes[part])
    return '\033[%sm' % ';'.join(map(str, codes))
