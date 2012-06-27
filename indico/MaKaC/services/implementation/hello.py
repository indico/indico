from MaKaC.services.implementation.base import ServiceBase, ParameterManager


class HelloUpperService(ServiceBase):
    def _checkParams(self):
        ServiceBase._checkParams(self)

        # ParameterManager handler parameter sanitization
        pm = ParameterManager(self._params)
        self._name = pm.extract("name", pType=str, allowEmpty = False)

    def _getAnswer(self):
        return self._name.upper()

methodMap = {
    "upper": HelloUpperService
}
