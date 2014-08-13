from functools import wraps

from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface.mail import GenericNotification


def email_sender(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        mails = fn(*args, **kwargs)
        if not isinstance(mails, list):
            mails = [mails]
        for mail in mails:
            GenericMailer.send(GenericNotification(mail))
    return wrapper
