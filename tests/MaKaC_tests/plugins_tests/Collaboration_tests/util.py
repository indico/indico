from ZEO.runzeo import ZEOOptions, ZEOServer

class TestZEOServer:
    def __init__(self, port, file):
        self.options = ZEOOptions();
        options.realize(['-f',file,'-a','localhost:%d' % port])
        self.server = ZEOServer(self.options)

    def start(self):
        self.server.main()
