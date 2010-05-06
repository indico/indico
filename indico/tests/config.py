import os

class TestConfig:
    __instance = None

    def __init__(self):
        execfile(os.path.join(os.path.dirname(__file__), 'tests.conf'))
        self.testsConf = locals()

    def __getattr__(self, attr):
        """Dynamic finder for values defined in indico.conf

            For example, if an indico.conf value is "username" this method will
            return its value for a getUsername() call.

            If you add a new pair option = value to indico.conf there is no need to
            create anything here. It will be returned automatically.

            This all means that changing the name of an indico.conf will force you
            to change all references in code to getOldOptionName to getNewOptionName
            including the reference in default_values in this file.
        """
        # The following code intercepts all method calls that start with get and are
        # not already defined (so you can still override a get method if you want)
        # and returns a closure that returns the value of the option being asked for
        if attr[0:3] == 'get':
            def configFinder(k):
                return self.testsConf[k]
            return lambda: configFinder(attr[3:])
        else:
            raise AttributeError

    @classmethod
    def getInstance(cls):
        if cls.__instance == None:
            cls.__instance = cls()
        return cls.__instance
