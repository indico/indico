from indico.core.extpoint import IListener

class IInstantMessagingListener(IListener):
    """ Inserts or deletes objects related to plugins in the DB. To do so, it retrieves the _storage parameter of the Plugin class,
        and then it inserts it in the DB according to the selected index policy """

    def createChatroom(self, obj, params):
        pass

    def editChatroom(self, obj, params):
        pass

    def deleteChatroom(self, obj, params):
        pass

    def addConference2Room(self, obj, params):
        """ When someone wants to re use a chat room for a different conference we need to add the conference
            to the conferences list in the chat room, but also to add the chat room in the IndexByConf index """
