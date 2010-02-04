from ZEO.runzeo import ZEOOptions, ZEOServer

class TestZEOServer:
    def __init__(self, port, fd):
        self.options = ZEOOptions();
        self.options.realize(['-f',fd,'-a','localhost:%d' % port])
        self.server = ZEOServer(self.options)

    def start(self):
        self.server.main()