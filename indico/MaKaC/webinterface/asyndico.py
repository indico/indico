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

