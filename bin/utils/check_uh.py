import MaKaC.webinterface.urlHandlers as uhs
from indico.web.flask.app import make_app
import importlib

app = make_app()

with app.test_request_context():
    mod_errors = []
    func_errors = []
    for attr in dir(uhs):
        if attr[:2] != 'UH':
            continue
        uh = getattr(uhs, attr)
        if getattr(uh, '_endpoint', None) is None:
            if getattr(uh, '_relativeURL', None) is None:
                pass  # print 'UH with no ep/ru: %r' % uh
            continue
        if uh._endpoint not in app.url_map._rules_by_endpoint:
            #print 'UH with invalid endpoint: %r' % uh
            try:
                assert uh._endpoint.startswith('legacy.')
            except AssertionError:
                print uh._endpoint
                raise
            ep = uh._endpoint.split('.', 1)[1]
            module_name, _, funcname = ep.partition('-')
            if not funcname:
                funcname = 'index'

            try:
                module = importlib.import_module('indico.htdocs.' + module_name)
            except ImportError:
                mod_errors.append('%s references invalid module %s' % (uh.__name__, module_name))
                continue
            try:
                getattr(module, funcname)
            except AttributeError:
                func_errors.append('%s references invalid function %s.%s' % (uh.__name__, module_name, funcname))
                continue
            else:
                print '%s references route missing for function %s.%s' % (uh.__name__, module_name, funcname)

    print '\n'.join(sorted(mod_errors))
    print
    print '\n'.join(sorted(func_errors))
