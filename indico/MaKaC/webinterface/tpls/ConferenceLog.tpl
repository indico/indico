<table width="100%" class="logsTab"><tr><td>
<script type="text/javascript">
<!--
function selectAll()
{
    //document.logListForm.trackShowNoValue.checked=true
    if (!document.logListForm.logItem.length){
        document.logListForm.logItem.checked=true
    } else {
        for (i = 0; i < document.logListForm.logItem.length; i++) {
            document.logListForm.logItem[i].checked=true
        }
    }
}

function deselectAll()
{
    //document.pendingForm.trackShowNoValue.checked=false
    if (!document.logListForm.logItem.length)    {
        document.logListForm.logItem.checked=false
    } else {
       for (i = 0; i < document.logListForm.logItem.length; i++) {
           document.logListForm.logItem[i].checked=false
       }
    }
}
//-->
</script>
<br>
<table width="100%" align="center" border="0">
    <tr>
        <td colspan="2" class="groupTitle"> ${ _("Event Log")}</td>
    </tr>
    <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
    <tr>
        <td colspan="2">
        ${ errorMsg }
        ${ infoMsg }
        </td>
    </tr>
    <form action=${ logFilterAction } method="post" name="logFilterForm">
    <tr>
        <td width="18%">
            &nbsp;<b> ${ _("Show standard views")}:</b>
        </td>
        <td>
            &nbsp;<input type="submit" class="btn" name="filter" value="${ _("General Log")}" />
            &nbsp;<input type="submit" class="btn" name="filter" value="${ _("Email Log")}" />
            &nbsp;<input type="submit" class="btn" name="filter" value="${ _("Action Log")}" />
        </td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td width="18%">
            &nbsp;<b> ${ _("Apply custom filter")}:</b>
        </td>
        <td>
            &nbsp;<input type="text" name="filterKey"  />
            &nbsp;<input type="submit" class="btn" name="filter" value="${ _("Custom Log")}" />
        </td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    </form>
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td colspan="2">
        <table border="0">
            <tr>
                <td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">

                    <a href="${ orderByDate }">${ _("Date")}</a>
                </td>
                <td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                    &nbsp;<a href="${ orderBySubject }"> ${ _("Subject")}</a>
                </td>
                <td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                    &nbsp;<a href="${ orderByResponsible }"> ${ _("Responsible")}</a>
                </td>
                <td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                    &nbsp;<a href="${ orderByModule }"> ${ _("Module")}</a>
                </td>
            </tr>
            <form action=${ logListAction } method="post" name="logListForm">
            ${ log }
            </form>
        </table>
        </td>
    </tr>
</table>
<br>
</td></tr></table>
