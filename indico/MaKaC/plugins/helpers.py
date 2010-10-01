from BTrees.OOBTree import OOBTree
from BTrees.OOBTree import OOTreeSet
from MaKaC.common.Counter import Counter
from MaKaC.plugins.base import PluginsHelper
from MaKaC.services.interface.rpc.common import ServiceError, NoReportError
from MaKaC.common.logger import Logger


class PluginFieldsHelper(PluginsHelper):
    """Provides a simple interface to access fields of a given plugin"""

    def __init__(self, pluginType, plugin):
        PluginsHelper.__init__(self, pluginType, plugin)

    def getOption(self, optionName):
        try:
            return self._plugin.getOption(optionName).getValue()
        except Exception, e:
            Logger.get('Plugins').error("Exception while trying to access the option %s in the plugin %s: %s" % (self._pluginType, self._plugin, str(e)))
            raise Exception("Exception while trying to access the option %s in the plugin %s: %s" % (self._pluginType, self._plugin, str(e)))

    def getAttribute(self, attribute):
        try:
            return getattr(self._plugin, attribute)
        except AttributeError:
            Logger.get('Plugins').error("No attribute %s in plugin %s" % (attribute, self._plugin))
            raise Exception("No attribute %s in plugin %s" % (attribute, self._plugin))

    def getStorage(self):
        return self._plugin.getStorage()

class DBHelpers:
    @classmethod
    def getChatRoot(cls):
         #pick the plugin
        pfh = PluginFieldsHelper('InstantMessaging', 'Jabber')
        #and the element from which objects will be hanging in the DB
        return pfh.getStorage()

    @classmethod
    def getCounter(cls):
        root = cls.getChatRoot()

        if not root.has_key('counter'):
            raise ServiceError( message=_('Expected index not found while accessing the database (counter)'))

        return root['counter']

    @classmethod
    def newID(cls, conf):
        return cls.getCounter().newCount()

    @classmethod
    def getChatroomList(cls, conf):
        root = cls.getChatRoot()
        conf = str(conf.getId())

        if not root.has_key('indexByConf'):
            raise ServiceError( message=_('Expected index not found while accessing the database (indexByConf)'))
        confRooms = root['indexByConf']
        if not confRooms.has_key(conf):
            raise ServiceError( message=_('Conference not found in database: %s' %conf))

        return confRooms[conf]

    @classmethod
    def getChatroom(cls, id):
        root = cls.getChatRoot()

        if not root.has_key('indexByID'):
            raise ServiceError( message=_('Expected index not found while accessing the database (indexByID)'))
        room = root['indexByID']
        if not room.has_key(id):
            raise ServiceError( message=_('Chat room not found in database: %s' %id))

        return room[id]

    @classmethod
    def roomsToShow(cls, conf):
        """ For the given conference, will return True if there is any chat room to be shown
            in the conference page, and will return False if there are not
        """
        try:
            chatrooms = cls.getChatroomList(conf)
        except Exception,e:
            return False
        #there are no chatrooms, there's nothing to show
        if len(chatrooms) is 0:
            return False
        for chatroom in chatrooms:
            if chatroom.getShowRoom():
                return True
        #all the rooms were set to be hidden from the users
        return False

    @classmethod
    def getShowableRooms(cls, conf):
        chatrooms = []
        try:
            for room in cls.getChatroomList(conf):
                if room.getShowRoom():
                    chatrooms.append(room)
        except Exception,e:
            return []
        return chatrooms

    @classmethod
    def getRoomsByUser(cls, user):
        """ Will return the chat rooms created by the requested user """
        root = cls.getChatRoot()
        userID = str(user['id'])
        if not root.has_key('indexByUser'):
            return []
        rooms = root['indexByUser']
        if not rooms.has_key(userID):
            return []

        return rooms[userID]


class IndexHelpers:

    def __init__(self, index, storingStructure=OOBTree):
        self._root = DBHelpers.getChatRoot()
        self._index = index
        self._storingStructure = storingStructure
        self._indexCheck()

    def _indexCheck(self):
        """ If the index doesn't exist we'll need to create it"""
        if not self._root.has_key(self._index):
            self._root[self._index] = self._storingStructure()
        self._indexToAccess = self._root[self._index]

    def _indexCheckDelete(self, element):
        if len( self._root[self._index][element] ) is 0:
            self._root[self._index].pop(element)

    def get(self):
        return self._indexToAccess

    def add(self, element):
        pass

    def delete(self, element):
        pass


class CounterIndexHelper(IndexHelpers):
    """ This index just takes the count of the next index that shall be given to a new chat room """

    def __init__(self):
        IndexHelpers.__init__(self, 'counter', Counter)


class IndexByConfHelper(IndexHelpers):
    """ Index by conference. Using the conference id as the key, there will be a OOTreeSet inside with all the existing chat rooms for that conference"""

    def __init__(self, conf):
        IndexHelpers.__init__(self, 'indexByConf')
        self._conf = conf

    def add(self, element):
        self._indexCheck()

        # self.get is equivalent to root['indexByConf']
        if not self.get().has_key(self._conf):
            self.get()[self._conf] = OOTreeSet()

        self.get()[self._conf].insert(element)

    def delete(self, element):
        self.get()[self._conf].remove(element)

        self._indexCheckDelete(self._conf)


class IndexByUserHelper(IndexHelpers):
    """ Index by user ID. We use a OOTreeSet to store the chat rooms"""

    def __init__(self, id):
        IndexHelpers.__init__(self, 'indexByUser')
        self._id = id

    def add(self, element):
        self._indexCheck()

        # self.get is equivalent to root['IndexByUser']
        if not self.get().has_key(self._id):
            self.get()[self._id] = OOTreeSet()

        self.get()[self._id].insert(element)

    def delete(self, element):
        self.get()[self._id].remove(element)

        self._indexCheckDelete(self._id)


class IndexByCRNameHelper(IndexHelpers):
    """ Index by chat room name. We allow chat rooms to have the same name if they are in different servers. For each key we use a OOTreeSet to store them"""

    def __init__(self, name):
        IndexHelpers.__init__(self, 'indexByCRName')
        self._name = name

    def add(self, element):
        self._indexCheck()

        # self.get is equivalent to root['IndexByCRName']
        if self.get().has_key(element.getTitle()):
            for cr in self.get()[element.getTitle()]:
                #if there is a chat room repeated in the server (either ours or an external one) we have a problem
                if cr.getTitle() == element.getTitle() and cr.getHost() == element.getHost():
                    raise NoReportError( _('There is already a chat room in that server with that name, please choose another one'))
        else:
            self.get()[element.getTitle()] = OOTreeSet()

        self.get()[element.getTitle()].insert(element)

    def delete(self, element, indexToRemove=''):
        #we may want to delete a different index of the one contained in the element
        #for example, for the chat room edition we want to delete the index of the
        #previous chat room name
        if indexToRemove != '':
            self.get()[indexToRemove].remove(element)
            self._indexCheckDelete(indexToRemove)
        else:
            self.get()[self._name].remove(element)
            self._indexCheckDelete(self._name)


class IndexByIDHelper(IndexHelpers):
    """ Index by chat room ID. Since there can only exist one index per chat room, for each key there will directly be the Chatroom object"""

    def __init__(self):
        IndexHelpers.__init__(self, 'indexByID')

    def add(self, element):
        self._indexCheck()

        # self.get is equivalent to root['IndexByID']
        if self.get().has_key(element.getId()):
            raise ServiceError( message=_('There is already a chat room with the same id'))

        self.get()[element.getId()] = element

    def delete(self, element):
        self.get().pop(element.getId())

