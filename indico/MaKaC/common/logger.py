import os, logging
import logging.handlers

from MaKaC.common.Configuration import Config

class ExtraIndicoFilter(logging.Filter):

    def filter(self, record):
        if record.name.split('.')[0] == 'indico':
            return 0
        return 1

class Logger:
    """
    Encapsulates the features provided by the standard logging module
    """

    config = Config.getInstance()
    
    __rootLogger = logging.getLogger('')

    __indicoFileHandler = logging.FileHandler(os.path.join(config.getLogDir(), 'indico.log'),'a')
    __otherFileHandler = logging.FileHandler(os.path.join(config.getLogDir(), 'other.log'),'a')

    __formatter = logging.Formatter('%(asctime)s %(name)-16s: %(levelname)-8s %(message)s')
    __indicoFileHandler.setFormatter(__formatter)
    __otherFileHandler.setFormatter(__formatter)
    __indicoFileHandler.addFilter(logging.Filter('indico'))
    __otherFileHandler.addFilter(ExtraIndicoFilter())

    serverName = config.getWorkerName()
    if not serverName:
        serverName = config.getHostNameURL()

    # TODO: add config option to disable this?
    __smtpHandler = logging.handlers.SMTPHandler(config.getSmtpServer(),
                                            'logger@%s' % serverName,
                                            config.getSupportEmail(),
                                            'Unexpected Exception occurred at %s' % serverName)

    __smtpHandler.addFilter(logging.Filter('indico'))
    __smtpHandler.setLevel(logging.ERROR)

    __rootLogger.addHandler(__indicoFileHandler)
    __rootLogger.addHandler(__otherFileHandler)
    __otherFileHandler.setLevel(logging.WARNING)
    __rootLogger.addHandler(__smtpHandler)

    # TODO: see savannah task
    # if it's debug mode, be more exhaustive
    #if DEBUG or HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive():
    #    __rootLogger.setLevel(logging.DEBUG)
    #else:
    #    __rootLogger.setLevel(logging.WARNING)

    __rootLogger.setLevel(logging.DEBUG)

    @classmethod
    def get(cls, module=''):
        return logging.getLogger('indico.'+module)
