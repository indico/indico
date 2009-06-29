import xmlrpclib

mcuAddress = "ccmcu40.in2p3.fr"
mcuProxy = xmlrpclib.ServerProxy("http://%s/RPC2" % mcuAddress)
mcuUser = "indico-support@cern.ch"
mcuPassword = "xK!34(25"

# RmsApi should be used to create conference
def CreateConference(**params):
    return invokeMethod("conference.create", params)

# RmsApi should be used to destroy conference
def DestroyConference(**params):
    return invokeMethod("conference.destroy", params)

def EnumerateConferences(**params):
    return invokeMethod("conference.enumerate", params)

def EnumerateAllConferences(**params):
    return enumerateAll(EnumerateConferences, "conferences", **params)
        
def SelectConferences(**params):
    return selectDictionaries(EnumerateAllConferences(**params), params)

def QueryConferenceStreaming(**params):
    return invokeMethod("conference.query", params)

def ModifyConference(**params):
    return invokeMethod("conference.modify", params)

def AddParticipant(**params):
    return invokeMethod("participant.add", params)

def RemoveParticipant(**params):
    return invokeMethod("participant.remove", params)

def EnumerateParticipants(**params):
    return invokeMethod("participant.enumerate", params)

def EnumerateAllParticipants(**params):
    return enumerateAll(EnumerateParticipants, "participants", **params)

def SelectParticipants(params, **filter):
    return selectDictionaries(EnumerateAllParticipants(**params), filter)

def ModifyParticipant(**params):
    return invokeMethod("participant.modify", params)

def ConnectParticipant(**params):
    return invokeMethod("participant.connect", params)

def DisconnectParticipant(**params):
    return invokeMethod("participant.disconnect", params)

def invokeMethod(name, params):
    args = {
        "authenticationUser": mcuUser,
        "authenticationPassword": mcuPassword
    }
    args.update(params)
    return getattr(mcuProxy, name)(args)

def enumerateAll(method, key, **params):
        id = None
        while True:
            if id == None:
                ret = method(**params)
            else:
                params["enumerateID"] = id
                ret = method(**params)
            for item in ret.get(key, []):
                yield item
            id = ret.get("enumerateID", None)
            if id == None:
                break

def selectDictionaries(dictionaries, pairs):
    return [dictionary for dictionary in dictionaries if hasAllPairs(dictionary, pairs)]

def hasAllPairs(target, source):
    for key, value in source.iteritems():
        if key not in target:
            return False
        if target[key] != value:
            return False
    return True

def first(list):
    if len(list) > 0:
        return list[0]
    else:
        return None
