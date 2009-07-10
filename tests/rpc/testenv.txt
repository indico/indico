from MaKaC.common import Config
from jsonrpc import ServiceProxy, JSONRPCException

import copy

indicoURL = Config().getBaseURL()

endPointURL = '%s/services/json-rpc' % indicoURL
endPoint = ServiceProxy(endPointURL)

def errorFrom(method, **kwargs):
    try:
        method(**kwargs)
	assert(False)
    except JSONRPCException, e:
        if e.error['code'] == 'ERR-P0' and e.error['inner']:
            print e.error['inner']
        elif e.error['code'] == 'ERR-P2':
            print e.error['message']
        return e.error['code']

def ordDict(dic):
    return sorted(dic.items())

def screwDict(dic, victimList):
    cDict = copy.copy(dic)
    for victim in victimList:
        cDict.pop(victim)
    return cDict

class testData:
    session1 = {
        'title':'Session 1',
        'description':'Description 1',
        'startDateTime': '27/11/2020 09:00',
        'endDateTime': '27/11/2020 11:00',
        'roomInfo': {'room': '',
                   'address': '',
                   'location': ''},
        'conveners': {
            '1': { 'firstName': 'John',
                 'familyName': 'Smith',
                 'email': 'johnsmith@example.com',
                 'affiliation': 'Atlantis Institute of Fictive Science' }
            }        
    }
    
    slot1 = {
        'title':'Slot 1',
        'dateTime': '27/11/2020 11:30',
        'duration': '60',
        'roomInfo': {'room': '',
                   'address': '',
                   'location': ''},
        'conveners': {}
    }
    
    contribution1 = {
        'title':'Contribution 1',
        'description':'description for a contribution',
        'dateTime':'27/11/2020 12:00',
        'duration':'30',
        'keywords':['test','meeting'],
        'presenters': {
            '1' : {
                'title': 'Dr',
                'firstName': 'Strange',
                'familyName': 'Love',
                'email': 'drstrangelove@example.com',
                'affiliation': 'Atlantis Institute of Fictive Science'
                }
            },
        'roomInfo': {'room': '',
                   'address': '',
                   'location': ''}
    }
