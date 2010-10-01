import zope.interface

class Component(object):
    def __init__(self):
        #the lowest one
        self.priority=10

    def getPriority(self):
        return self.priority

class IListener(zope.interface.Interface):
    pass

class IContributor(zope.interface.Interface):
    pass



class IManagementEventsListener(zope.interface.Interface):
    """Events that are related to the management of a conference"""

    def notifyDateChange(self, obj, params):
        pass

    def notifyStartDateChange(self, obj, params):
        pass

    def notifyStartTimeChange(self, obj, sdate):
        pass

    def notifyEndTimeChange(self, obj, edate):
        pass

    def notifySetTimezone(self, obj, oldTimezone):
        pass

    def notifyEndDateChange(self, obj, params):
        pass

    def notifyTitleChange(self, obj, params):
        pass

    def notifyDelete(self, obj, params):
        pass


class IInstantMessagingListener(zope.interface.Interface):
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


class INavigationContributor(zope.interface.Interface):
    """Events that fill the sidemenu of a conference with the activated plugins.
       You may want a reference to know how to implement these methods. You can check the components file for
       Jabber (MaKaC.plugins.InstantMessaging.Jabber)
    """

    def fillManagementSideMenu(self, obj, params):
        """ Inserts an element in the conference management's side menu"""

    def confDisplaySMFillDict(self, obj, params):
        """ Conference Display Side Menu Fill Dictionary.
            This dictionary is used to store all your new items on the side menu of the conference display.
            In the core, there is a dictionary called self._linkData in which the elements to be showed
            in the conference display side menu are inserted.
        """

    def confDisplaySMFillOrderedKeys(self, obj, list):
        """ Conference Display Side Menu Fill Ordered Keys.
            Right next to the dictionary there is a list with the ordered keys, we need to include them also
        """

    def confDisplaySMShow(self, obj, params):
        """ Adds our element to the list of elements to be showed in the side menu of the conference main page"""

    def meetingAndLectureDisplay(self, obj, params):
        """ Adds our element to the list of elements to be showed in the main menu of a meeting or a lecture"""

    def getActiveNavigationItem(self, obj, params):
        pass

