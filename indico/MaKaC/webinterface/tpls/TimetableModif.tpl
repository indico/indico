<%inherit file="SystemLinkModif.tpl"/>
<%block name="additionalOptions">
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Default view")}</span></td>
        <form action="${toggleTimetableViewURL}" method="post">
            <td width="100%" style="padding:0em 0em 0em 1em; font-weight:bold; background-color:white;">
                ${ viewMode } <input type="submit" class="btn" value="${changeViewModeTo}"/>
            </td>
        </form>
    </tr>
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat"> ${_("Default layout")}</span>
        </td>
        <form action="${toggleTTDefaultLayoutURL}" method="post">
            <td width="100%" style="padding:0em 0em 0em 1em; font-weight:bold; background-color:white;">
                ${ defaultTTLayout } <input type="submit" class="btn" value="${changedefaultTTLayoutTo}"/>
            </td>
        </form>
    </tr>
</%block>
