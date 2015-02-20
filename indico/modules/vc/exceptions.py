class VCRoomError(Exception):
    def __init__(self, message, field=None):
        super(VCRoomError, self).__init__(message)
        self.message = message
        self.field = field


class VCRoomNotFoundError(VCRoomError):
    def __init__(self, message):
        super(VCRoomNotFoundError, self).__init__(message)
