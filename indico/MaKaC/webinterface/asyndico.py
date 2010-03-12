from MaKaC.services.interface.rpc.offline import offlineRequest

class macros:

    FIELD_TEXT = 'textField'
    FIELD_RICHTEXT = 'richTextField'
    FIELD_SELECT = 'selectionField'
    FIELD_DATE = 'dateEditor'

    @classmethod
    def genericField(cls, dataType, domId, method, params, preCache=False, rh=None, options = None, orderOptionsBy = None):
        """ orderOptionsBy can have the following values: None (no order), 'key', 'value'
            use for options that come as a Python dictionary
        """

        if preCache:
            if not rh:
                raise Exception('Precaching of RPC values requires a request handler to be specified!')

            cacheDef = ",%s" % offlineRequest(rh, method, params)
        else:
            cacheDef = ''

        if dataType == cls.FIELD_SELECT:

            if (type(options) == dict and orderOptionsBy is not None):

                tupleList = options.items()
                if orderOptionsBy == 'key':
                    tupleList = sorted(tupleList, key=lambda t: t[0])
                else:
                    tupleList = sorted(tupleList, key=lambda t: t[1])

                optionsDef = "".join([", {",
                                      ", ".join(["'" + str(key) + "' : '" + str(value) + "'" for key, value in tupleList]),
                                      "}"])

            else:
                optionsDef = ",%s" % options

        elif dataType == cls.FIELD_RICHTEXT:
            optionsDef = ", %s, %s" % (options[0], options[1])

        else:
            optionsDef = ''


        return """new IndicoUI.Widgets.Generic.%s($E('%s'),
                    '%s', %s%s%s);\n""" % (
                    dataType,
                    domId,
                    method,
                    params,
                    optionsDef,
                    cacheDef
                    )


