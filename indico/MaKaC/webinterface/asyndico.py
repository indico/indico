from MaKaC.services.interface.rpc.offline import offlineRequest
from MaKaC.common.fossilize import fossilize


class UserDataGenerator(object):

    def generate(self):
        """
        To be overridden
        """

    def __init__(self, user):
        self._user = user

class UserDataFavoriteUserListGenerator(UserDataGenerator):
    """
    """

    def generate(self):
        return fossilize(self._user.getPersonalInfo().getBasket().getUsers())

class UserDataFavoriteUserIdListGenerator(UserDataGenerator):
    """
    """

    def generate(self):
        return dict((userId, True) for userId in
                    self._user.getPersonalInfo().getBasket().getUsers())


class UserDataFactory(object):
    """
    Registers the different types of user data that
    might be needed for the client-side
    """

    # Any new "user data packages" should be added here
    _registry = {
        'favorite-user-list': UserDataFavoriteUserListGenerator,
        'favorite-user-ids': UserDataFavoriteUserIdListGenerator
        }

    def build(self, packageName):
        return self._registry[packageName](self._user).generate()

    def __init__(self, user):
        self._user = user

class macros:

    FIELD_TEXT = 'textField'
    FIELD_RICHTEXT = 'richTextField'
    FIELD_SELECT = 'selectionField'
    FIELD_DATE = 'dateEditor'

    @classmethod
    def genericField(cls, dataType, domId, method, params, preCache=False, rh=None, options = None, orderOptionsBy = None):
        """ orderOptionsBy can have the following values: None (no order), 'key', 'value'
            use for options that come as a Python dictionary
        """

        if preCache:
            if not rh:
                raise Exception('Precaching of RPC values requires a request handler to be specified!')

            cacheDef = ",%s" % offlineRequest(rh, method, params)
        else:
            cacheDef = ''

        if dataType == cls.FIELD_SELECT:

            if (type(options) == dict and orderOptionsBy is not None):

                tupleList = options.items()
                if orderOptionsBy == 'key':
                    tupleList = sorted(tupleList, key=lambda t: t[0])
                else:
                    tupleList = sorted(tupleList, key=lambda t: t[1])

                optionsDef = "".join([", {",
                                      ", ".join(["'" + str(key) + "' : '" + str(value) + "'" for key, value in tupleList]),
                                      "}"])

            else:
                optionsDef = ",%s" % options

        elif dataType == cls.FIELD_RICHTEXT:
            optionsDef = ", %s, %s" % (options[0], options[1])

        else:
            optionsDef = ''


        return """new IndicoUI.Widgets.Generic.%s($E('%s'),
                    '%s', %s%s%s);\n""" % (
                    dataType,
                    domId,
                    method,
                    params,
                    optionsDef,
                    cacheDef
                    )


