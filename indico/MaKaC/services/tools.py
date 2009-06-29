
def toJsDate(datetime):
    return "(new Date(%i,%i,%i,%i,%i,%i))" % (datetime.year,
                                              datetime.month - 1,
                                              datetime.day,
                                              datetime.hour,
                                              datetime.minute,
                                              datetime.second)
