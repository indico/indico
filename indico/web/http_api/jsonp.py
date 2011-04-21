from indico.util.metadata.json import JSONSerializer


class JSONPSerializer(JSONSerializer):
    """
    Just adds prefix
    """

    _mime = 'application/javascript'

    def __init__(self, jsonp='read', **kwargs):
        super(JSONPSerializer, self).__init__(**kwargs)
        self._prefix = jsonp

    def __call__(self, results):
        return "// fetched from Indico\n%s(%s);" % \
               (self._prefix,
                super(JSONPSerializer, self).__call__(results))
