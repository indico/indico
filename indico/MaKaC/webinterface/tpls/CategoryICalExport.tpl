<%inherit file="ICalExportBase.tpl"/>
<%block name="downloadText">${_('Download current category:')}</%block>
<%block name="script" args="item">
    ${parent.script(item)}
    <script type="text/javascript">
       exportPopups["${item.getUniqueId()}"] = new ExportIcalInterface(${apiMode | n, j}, ${persistentUserEnabled | n,j}, ${persistentAllowed | n,j}, ${apiActive | n,j}, ${userLogged | n,j}, setURLs, 'category.api.getExportURLs', {categId:"${item.getId()}"}, ${requestURLs | n,j}, "${item.getUniqueId()}", "${currentUser.getId() if currentUser else ''}");
    </script>
</%block>
