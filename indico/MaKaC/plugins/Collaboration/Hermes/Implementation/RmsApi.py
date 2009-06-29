import xmlrpclib

rmsProxy = xmlrpclib.ServerProxy("http://rms.in2p3.fr/rpc/RMS_srv.php")
rmsUser = "indico-support@cern.ch"
rmsPassword = "xK!34(25"

def timeDeltaToMinutes(delta):
    return delta.seconds / 60 + delta.days * 1440

def responseToMap(text):
    map = {}
    for entry in text.split(","):
        key, value = entry.split(":", 1)
        map[key] = value
    return map

def CreateConference(name, start, end, pin, h239):
    startDate = str(start.year).rjust(2, "0") + "-" + str(start.month).rjust(2, "0") + "-" + str(start.day).rjust(2, "0")
    if (h239):
        h239 = "on"
    else:
        h239 = "null"
    if (pin == None):
        pin = ""
    else:
        pin = str(pin)
    lengthMinutes = timeDeltaToMinutes(end - start)
    lengthHours, lengthMinutes = divmod(lengthMinutes, 60)
    response = rmsProxy.RMScreate_conf(startDate,
                                       str(start.hour).rjust(2, "0"), str(start.minute).rjust(2, "0"),
                                       str(lengthHours).rjust(2, "0"), str(lengthMinutes).rjust(2, "0"),
                                       name, pin, h239, rmsUser, rmsPassword)
    map = responseToMap(response)
    return (map["ConfID"], map["PINCode"])
    
def DeleteConference(id):
    response = rmsProxy.RMSdelete_conf(id, rmsUser, rmsPassword)
    if (response != "Succes"): # RMS spelling bug
        raise Exception(response)
    
