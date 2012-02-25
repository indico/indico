import os, string, copy
import logging.handlers, logging.config, logging
import ConfigParser

from MaKaC.common.Configuration import Config
from MaKaC.common.contextManager import ContextManager

class ExtraIndicoFilter(logging.Filter):

    def filter(self, record):
        if record.name.split('.')[0] == 'indico':
            return 0
        return 1

class IndicoMailFormatter(logging.Formatter):
    def format(self, record):
        s = logging.Formatter.format(self, record)
        return s + self._getRequestInfo()

    def _getRequestInfo(self):
        rh = ContextManager.get('currentRH', None)
        if not rh:
            return ''
        info = ['Additional information:']
        info.append('URL: %s' % rh.getRequestURL())
        info.append('Params: %s' % rh._getTruncatedParams())
        info.append('IP: %s' % rh._req.remote_ip)
        info.append('User Agent: %s' % rh._req.headers_in.get('User-Agent', 'n/a'))
        info.append('Referer: %s' % rh._req.headers_in.get('Referer', 'n/a'))
        return '\n\n%s' % '\n'.join(info)

class LoggerUtils:

    @classmethod
    def configFromFile(cls, fname, defaultArgs, filters):
        """
        Read the logging configuration from the logging.conf file.
        Fetch default values if the logging.conf file is not set.
        """

        if not os.path.exists(fname):
            return

        cp = ConfigParser.ConfigParser()
        if hasattr(cp, 'readfp') and hasattr(fname, 'readline'):
            cp.readfp(fname)
        else:
            cp.read(fname)

        try:
            formatters = logging.config._create_formatters(cp)
        except:
            #TODO: this is just for backwards compatibility. It should be removed in v0.98 with p2.6
            formatters = cls._create_formatters(cp)

        # Really ugly.. but logging fails to import MaKaC.common.logger.IndicoMailFormatter
        # when using it in the class= option...
        if 'mailFormatter' in formatters:
            f = formatters['mailFormatter']
            formatters['mailFormatter'] = IndicoMailFormatter(f._fmt, f.datefmt)

        logging._acquireLock()
        try:
            logging._handlers.clear()
            del logging._handlerList[:]
            handlers = cls._install_handlers(cp, defaultArgs, formatters, filters)
            logging.config._install_loggers(cp, handlers, False)

        finally:
            logging._releaseLock()
        return handlers

    @classmethod
    def _install_handlers(self, cp, defaultArgs, formatters, filters = None):
        """
        Install and return handlers. If a handler configuration
        is missing its args, fetches the default values from the
        indico.conf file
        """
        hlist = cp.get("handlers", "keys")
        if not len(hlist):
            return {}
        hlist = hlist.split(",")
        handlers = {}
        fixups = [] #for inter-handler references

        for hand in hlist:
            sectname = "handler_%s" % hand.strip()
            klass = cp.get(sectname, "class")
            opts = cp.options(sectname)
            if "formatter" in opts:
                fmt = cp.get(sectname, "formatter")
            else:
                fmt = ""
            klass = eval(klass, vars(logging))
            if "args" in opts :
                # if the args are not present in the file,
                # take default values
                args = cp.get(sectname, "args")
            else :
                try:
                    args = defaultArgs[hand.strip()]
                except KeyError:
                    continue
            args = eval(args, vars(logging))
            h = apply(klass, args)
            if "level" in opts:
                level = cp.get(sectname, "level")
                h.setLevel(logging._levelNames[level])
            if len(fmt):
                h.setFormatter(formatters[fmt])
            if filters and hand.strip() in filters:
                for fltr in filters[hand.strip()]:
                    h.addFilter(fltr)
            #temporary hack for FileHandler and MemoryHandler.
            if klass == logging.handlers.MemoryHandler:
                if "target" in opts:
                    target = cp.get(sectname,"target")
                else:
                    target = ""
                if len(target): #the target handler may not be loaded yet, so keep for later...
                    fixups.append((h, target))
            handlers[hand] = h
        #now all handlers are loaded, fixup inter-handler references...
        for h, t in fixups:
            h.setTarget(handlers[t])
        return handlers

    @classmethod
    def _create_formatters(cls, cp):
        #TODO: this is just for backwards compatibility. It should be removed in v0.98 with p2.6
        flist = cp.get("formatters", "keys")
        if len(flist):
            flist = string.split(flist, ",")
            formatters = {}
            for form in flist:
                sectname = "formatter_%s" % form
                opts = cp.options(sectname)
                if "format" in opts:
                    fs = cp.get(sectname, "format", 1)
                else:
                    fs = None
                if "datefmt" in opts:
                    dfs = cp.get(sectname, "datefmt", 1)
                else:
                    dfs = None
                f = logging.Formatter(fs, dfs)
                formatters[form] = f
            return formatters
        return {}

    @classmethod
    def _install_loggers(cls, cp, handlers):
        #TODO: this is just for backwards compatibility. It should be removed in v0.98 with p2.6
        llist = cp.get("loggers", "keys")
        llist = string.split(llist, ",")
        llist.remove("root")
        sectname = "logger_root"
        root = logging.root
        log = root
        opts = cp.options(sectname)
        if "level" in opts:
            level = cp.get(sectname, "level")
            log.setLevel(logging._levelNames[level])
        for h in root.handlers[:]:
            root.removeHandler(h)
        hlist = cp.get(sectname, "handlers")
        if len(hlist):
            hlist = string.split(hlist, ",")
            for hand in hlist:
                log.addHandler(handlers[hand])
        #and now the others...
        #we don't want to lose the existing loggers,
        #since other threads may have pointers to them.
        #existing is set to contain all existing loggers,
        #and as we go through the new configuration we
        #remove any which are configured. At the end,
        #what's left in existing is the set of loggers
        #which were in the previous configuration but
        #which are not in the new configuration.
        existing = root.manager.loggerDict.keys()
        #now set up the new ones...
        for log in llist:
            sectname = "logger_%s" % log
            qn = cp.get(sectname, "qualname")
            opts = cp.options(sectname)
            if "propagate" in opts:
                propagate = cp.getint(sectname, "propagate")
            else:
                propagate = 1
            logger = logging.getLogger(qn)
            if qn in existing:
                existing.remove(qn)
            if "level" in opts:
                level = cp.get(sectname, "level")
                logger.setLevel(logging._levelNames[level])
            for h in logger.handlers[:]:
                logger.removeHandler(h)
            logger.propagate = propagate
            logger.disabled = 0
            hlist = cp.get(sectname, "handlers")
            if len(hlist):
                hlist = string.split(hlist, ",")
                for hand in hlist:
                    logger.addHandler(handlers[hand])
        #Disable any old loggers. There's no point deleting
        #them as other threads may continue to hold references
        #and by disabling them, you stop them doing any logging.
        for log in existing:
            root.manager.loggerDict[log].disabled = 1


class Logger:
    """
    Encapsulates the features provided by the standard logging module
    """

    @classmethod
    def initialize(cls):
        import pydevd;pydevd.settrace()
        # Lists of filters for each handler
        filters = {'indico' : [logging.Filter('indico')],
                   'other'  : [ExtraIndicoFilter()],
                   'smtp'   : [logging.Filter('indico')]}

        config = Config.getInstance()
        logConfFilepath = os.path.join(config.getConfigurationDir(), "logging.conf")

        configDir = config.getLogDir()
        smtpServer = config.getSmtpServer()
        serverName = config.getWorkerName()
        if not serverName:
            serverName = config.getHostNameURL()

        # Default arguments for the handlers, taken mostly for the configuration
        defaultArgs = { 'indico' : "('%s', 'a')" % os.path.join(configDir, 'indico.log'),
                        'other'  : "('%s', 'a')" % os.path.join(configDir, 'other.log'),
                        'smtp'   : "(\"%s\", 'logger@%s', ['%s'], 'Unexpected Exception occurred at %s')"
                        % (smtpServer[0], serverName, config.getSupportEmail(), serverName)
                    }

        cls.handlers = LoggerUtils.configFromFile(logConfFilepath, defaultArgs, filters)
    @classmethod
    def reset(cls):
        """
        Reset the config, using new paths, etc (useful for testing)
        """
        if cls.handlers:
            for handler in copy.copy(cls.handlers):
                cls.removeHandler(handler)

        cls.initialize()

    @classmethod
    def removeHandler(cls, handlerName):
        if cls.handlers:
            handler = cls.handlers.get(handlerName)

            if handler:
                del cls.handlers[handlerName]
                logging.root.handlers.remove(handler)

    @classmethod
    def get(cls, module=None):
        return logging.getLogger('indico' if module == None else 'indico.' + module)


Logger.initialize()
