import os, logging.config
import logging.handlers

from MaKaC.common.Configuration import Config
import ConfigParser

class ExtraIndicoFilter(logging.Filter):

    def filter(self, record):
        if record.name.split('.')[0] == 'indico':
            return 0
        return 1

class LoggerUtils:

    @classmethod
    def configFromFile(self, fname, defaultArgs, filters):
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

        formatters = logging.config._create_formatters(cp)

        logging._acquireLock()
        try:
            logging._handlers.clear()
            del logging._handlerList[:]
            handlers = self._install_handlers(cp, defaultArgs, formatters, filters)
            try:
                logging.config._install_loggers(cp, handlers)
            except TypeError:
                logging.config._install_loggers(cp, handlers, False)

        finally:
            logging._releaseLock()

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

class Logger:
    """
    Encapsulates the features provided by the standard logging module
    """

    config = Config.getInstance()

    configDir = config.getLogDir()
    smtpServer = config.getSmtpServer()
    serverName = config.getWorkerName()
    if not serverName:
        serverName = config.getHostNameURL()

    # Default arguments for the handlers, taken mostly for the configuration
    defaultArgs = { 'indico' : "('%s', 'a')" %os.path.join(configDir, 'indico.log'),
                    'other'  : "('%s', 'a')" %os.path.join(configDir, 'other.log'),
                    'smtp'   : "('%s', 'logger@%s', ['%s'], 'Unexpected Exception occurred at %s')"
                                %(smtpServer, serverName, config.getSupportEmail(), serverName)
                    }

    # Lists of filters for each handler
    filters = {'indico' : [logging.Filter('indico')],
               'other'  : [ExtraIndicoFilter()],
               'smtp'   : [logging.Filter('indico')]}

    logConfFilepath = os.path.join(config.getConfigurationDir(), "logging.conf")

    #logging.config.fileConfig(logConfFilepath)
    LoggerUtils.configFromFile(logConfFilepath, defaultArgs, filters)

    @classmethod
    def get(cls, module=''):
        return logging.getLogger('indico.'+module)
