<table>
<tr>
    <td class="groupTitle">${ itemNumber }</td>
    <td>
        <table>
        <tr>
            <td>Type:
                <select name="${ materialTypeSelectFieldName }">
                    ${ matTypeItems }
                </select>
                or <input name="${ materialTypeInputFieldName }" size="25" value="${ materialTypeInputFieldValue }">
            </td>
        </tr>
        <tr>
            <td> ${ _("URL to File")}:
                <input name="${ urlFieldName }" value="${ linkValue }">
            </td>
        </tr>
        </table>
    </td>
</tr>
</table>
