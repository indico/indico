<%inherit file="ICalExportBase.tpl"/>
<%block name="downloadText">${_('Download current category:')}</%block>
<%block name="script">
<script type="text/javascript">

var setURLs = function(urls){
    $('#publicLink${categ.getUniqueId()}').attr('value', urls["publicRequestURL"]);
    $('#publicLink${categ.getUniqueId()}').attr('title', urls["publicRequestURL"]);
    $('#authLink${categ.getUniqueId()}').attr('value', urls["authRequestURL"]);
    $('#authLink${categ.getUniqueId()}').attr('title', urls["authRequestURL"]);
};

exportPopups["${categ.getUniqueId()}"] = new ExportIcalInterface(${apiMode}, ${persistentUserEnabled | n,j}, ${persistentAllowed | n,j}, ${apiActive | n,j}, ${userLogged | n,j}, setURLs, 'category.api.getExportURLs', {categId:"${categ.getId()}"}, ${requestURLs | n,j}, "${categ.getUniqueId()}");

</script>
</%block>

