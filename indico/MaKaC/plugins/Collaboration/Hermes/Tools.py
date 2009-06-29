

def parseTime(text):
    from time import strptime
    from datetime import datetime
    return datetime(*strptime(text, "%Y-%m-%dT%H:%M:%S")[:6]) # magic:)
