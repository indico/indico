import pytz

class Conversion:
    @classmethod
    def datetime(cls, dt, tz = None):
        if dt:
            if tz:
                if isinstance(tz, basestring):
                    tz = pytz.timezone(tz)
                date = dt.astimezone(tz)
            else:
                date = dt
            return {'date': str(date.date()), 'time': str(date.time())}
        else:
            return None

    @classmethod
    def duration(cls, duration, units = 'minutes', truncate = True):
        if duration:
            from MaKaC.common.utils import formatDuration
            return formatDuration(duration, units, truncate)
        else:
            return None

    @classmethod
    def roomName(cls, room):
        if room:
            return room.getName()
        else:
            return ''

    @classmethod
    def locationName(cls, loc):
        if loc:
            return loc.getName()
        else:
            return ''

    @classmethod
    def locationAddress(cls, loc):
        if loc:
            return loc.getAddress()
        else:
            return ''

    @classmethod
    def parentSession(cls, entry):
        from MaKaC.schedule import ContribSchEntry, BreakTimeSchEntry
        from MaKaC.conference import SessionSlot

        session = None
        owner = entry.getOwner()

        if type(entry) == ContribSchEntry or (type(entry) == BreakTimeSchEntry and type(owner) == SessionSlot):
            session = owner.getSession()

        if session:
            return session.getId()
        else:
            return None

    @classmethod
    def parentSlot(cls, entry):
        from MaKaC.schedule import ContribSchEntry, BreakTimeSchEntry
        from MaKaC.conference import SessionSlot, Session

        slot = None

        if type(entry) == ContribSchEntry:
            contrib = entry.getOwner()
            session = contrib.getSession()

            # If the contribution is not owned by a session return nothing
            if type(session) != Session:
                return None

            # TODO: This should be fixed. There's currently no easy way
            # of knowing in which session slot a contribution belongs.
            # Loop through all the session slots and look if the contribution
            # exists in the schedule.
            for sl in session.getSlotList():
                for e in sl.getEntries():
                    if e.getOwner() == contrib:
                        slot = sl
                        break

        elif type(entry) == BreakTimeSchEntry:
            slot = entry.getOwner()

        if slot and type(slot) == SessionSlot:
            return slot.getId()
        else:
            return None

    @classmethod
    def sessionList(cls, event):
        sessions = {}
        for session in event.getSessionList():
            sessions[session.getId()] = session;
        return sessions

    @classmethod
    def locatorString(cls, obj):
        locator = obj.getOwner().getLocator()
        if not locator.has_key('sessionId'):
            if locator.has_key('contribId'):
                return "c%(contribId)s" % locator
            else:
                return ""
        elif not locator.has_key('contribId'):
            return "s%(sessionId)sl%(slotId)s" % locator
        else:
            return "s%(sessionId)sc%(contribId)s" % locator

    @classmethod
    def timedelta(cls, obj):
        """
        Converts a timedelta to integer minutes
        """
        return int(obj.seconds / 60)
