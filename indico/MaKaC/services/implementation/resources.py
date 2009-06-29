from MaKaC.services.implementation.base import ServiceBase
from MaKaC.services.interface.rpc.common import ServiceError
from MaKaC.common import Config
from MaKaC import i18n

class GetFileTypeIcon(ServiceBase):
    
    def _checkParams(self):
  
        self._fileType = self._params.get('fileType',None)
    
        if (self._fileType == None):
            raise ServiceError("ERR-MR0", "File type was not specified")
    
    def _getAnswer(self):
        cfg = Config.getInstance()
        url = cfg.getFileTypeIconURL(self._fileType)
        
        if url == "":
            return None
        else:
            return url

class GetTimezones(ServiceBase):
    
    def _getAnswer(self):
        cfg = Config.getInstance()
        return cfg.getTimezoneList()
        
class GetLanguages(ServiceBase):
    
    def _getAnswer(self):
        # the language list comes in an 'exotic' format
        # [["en_US","English (US)"],...]
        # we're better off returning a dictionary
        languages = {}
        for lang in i18n.langList():
            languages[lang[0]] = lang[1]

        return languages
