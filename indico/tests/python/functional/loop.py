import sys
if __name__ == '__main__':
    indicoPath = '~/workspace/cds-indico'
    seleniumToTest = '~/workspace/cds-indico/tests/python/functional/example_test.py:ExampleTest.testCreateDeleteLecture'

    sys.path = [indicoPath] + [indicoPath + '/indico'] + sys.path

    import nose
    from tests.Indicop import Indicop, Functional
    from tests.TestsConfig import TestsConfig
    from tests.util import TestZEOServer
    from MaKaC.common.Configuration import Config

    indicop = Indicop(None, None)
    dbSig = 0

    #checking if production db is running
    server = TestZEOServer(Config.getInstance().getDBConnectionParams()[1], 'test')
    if server.server.can_connect(server.options.family, server.options.address):
        print """Your production database is currently running.
Do you want to stop it using this command '%s' and run the tests?
(We will restart your produduction after the tests with this command '%s')""" % \
(TestsConfig.getInstance().getStopDBCmd(), TestsConfig.getInstance().getStartDBCmd())

        userInput = raw_input("Press enter or type 'yes' to accept: ")
        if userInput == 'yes' or userInput == '':
            dbSig = 3
        else:
            print "Exiting loop..."
            sys.exit(1)
    else:
        dbSig = 2

    indicop.startManageDB(dbSig)
    func = Functional()
    func.startSeleniumServer()

    try:
        for i in range(1, 10):
            print "\n##### Run number %s #####\n" % i
            args = ['nose', '-v', seleniumToTest]
            result = nose.run(argv = args)
            if not result:
                break
        else:
            print "\n##############################################################"
            print " Congratulations! Your functional test passed the loop test!"
            print "##############################################################\n"
    finally:
        func.stopSeleniumServer()
        indicop.stopManageDB(dbSig)