<%inherit file="ICalExportBase.tpl"/>
<%block name="downloadText">${_('Download current session:')}</%block>
<%block name="script">
    <script type="text/javascript">

    var setURLs = function(urls){
        $('#publicLink${session.getUniqueId()}').attr('value', urls["publicRequestURL"]);
        $('#publicLink${session.getUniqueId()}').attr('title', urls["publicRequestURL"]);
        $('#authLink${session.getUniqueId()}').attr('value', urls["authRequestURL"]);
        $('#authLink${session.getUniqueId()}').attr('title', urls["authRequestURL"]);
    };

    exportPopups["${session.getUniqueId()}"] = new ExportIcalInterface(${apiMode}, ${persistentUserEnabled | n,j}, ${persistentAllowed | n,j}, ${apiActive | n,j}, ${userLogged | n,j}, setURLs, 'schedule.api.getSessionExportURLs', {confId:"${session.getConference().getId()}", sessionId:"${session.getId()}"}, ${requestURLs | n,j}, "${session.getUniqueId()}");

    </script>
</%block>

