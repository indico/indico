<%inherit file="ICalExportBase.tpl"/>
<%block name="downloadText">${_('Download current contribution:')}</%block>
<%block name="script">
    <script type="text/javascript">

    var setURLs = function(urls){
        $('#publicLink${Contribution.getUniqueId()}').attr('value', urls["publicRequestURL"]);
        $('#publicLink${Contribution.getUniqueId()}').attr('title', urls["publicRequestURL"]);
        $('#authLink${Contribution.getUniqueId()}').attr('value', urls["authRequestURL"]);
        $('#authLink${Contribution.getUniqueId()}').attr('title', urls["authRequestURL"]);
    };

    exportPopups["${Contribution.getUniqueId()}"] = new ExportIcalInterface(${apiMode}, ${persistentUserEnabled | n,j}, ${persistentAllowed | n,j}, ${apiActive | n,j}, ${userLogged | n,j}, setURLs, 'schedule.api.getContribExportURLs', {confId:"${Contribution.getConference().getId()}", contribId:"${Contribution.getId()}"}, ${requestURLs | n,j}, "${Contribution.getUniqueId()}");

    </script>
</%block>

