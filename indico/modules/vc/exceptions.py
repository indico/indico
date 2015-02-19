class VCRoomError(Exception):
    def __init__(self, message, field=None):
        super(VCRoomError, self).__init__(message)
        self.message = message
        self.field = field
