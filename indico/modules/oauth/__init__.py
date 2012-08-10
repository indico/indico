from indico.core.index import OOIndex
from indico.core.extpoint.index import ICatalogIndexProvider
from MaKaC.common.logger import Logger
from zope.interface import Interface, implements
from indico.core.extpoint.base import Component

ACCESS_TOKEN_TTL = 10800 # 3 hours in seconds

class IIndexableByUserId(Interface):
    pass


class UserOAuthRequestTokenIndex(OOIndex):

    def __init__(self):
        super(UserOAuthRequestTokenIndex, self).__init__(IIndexableByUserId)

    def initialize(self, dbi=None):
        pass


class CatalogIndexProvider(Component):
    implements(ICatalogIndexProvider)

    def catalogIndexProvider(self, obj):
        return [('user_oauth_request_token', UserOAuthRequestTokenIndex)]


class UserOAuthAccessTokenIndex(OOIndex):

    def __init__(self):
        super(UserOAuthAccessTokenIndex, self).__init__(IIndexableByUserId)

    def initialize(self, dbi=None):
        pass


class CatalogIndexProvider(Component):
    implements(ICatalogIndexProvider)

    def catalogIndexProvider(self, obj):
        return [('user_oauth_access_token', UserOAuthAccessTokenIndex)]


class IIndexableByConsumerName(Interface):
    pass


class ConsumerOAuthRequestTokenIndex(OOIndex):

    def __init__(self):
        super(ConsumerOAuthRequestTokenIndex, self).__init__(IIndexableByConsumerName)

    def initialize(self, dbi=None):
        pass


class CatalogIndexProvider(Component):
    implements(ICatalogIndexProvider)

    def catalogIndexProvider(self, obj):
        return [('consumer_oauth_request_token', ConsumerOAuthRequestTokenIndex)]
