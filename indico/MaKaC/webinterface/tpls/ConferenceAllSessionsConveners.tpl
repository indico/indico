<script type="text/javascript">
<!--
function selectAll()
{
if (!document.convenersForm.conveners.length)
        {
            document.convenersForm.conveners.checked=true
        }else{
for (i = 0; i < document.convenersForm.conveners.length; i++)
    {
    document.convenersForm.conveners[i].checked=true
    }
}
}

function unselectAll()
{
if (!document.convenersForm.conveners.length)
        {
            document.convenersForm.conveners.checked=false
        }else{
for (i = 0; i < document.convenersForm.conveners.length; i++)
    {
    document.convenersForm.conveners[i].checked=false
    }
}
}
//-->
</script>
<table width="100%">
    <tr>
        <td>
            <a name="allSessionsConveners"></a>
            <table align="center" width="100%" border="0" style="border-left: 1px solid #777777;" cellpadding="0" cellspacing="0">
                <tr>
                    <td colspan="9" style="background:#E5E5E5; color:gray">

                        <table cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td colspan=2 class="groupTitle" width="100%">&nbsp;&nbsp;&nbsp; ${ _("All Sessions' Convener List")} (${ convenerNumber })</td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td colspan="9">&nbsp;</td>
                </tr>
                <form action=${ convenerSelectionAction } method="post" target="_blank" name="convenersForm">
                <tr>
                    ${ columns }
                    ${ conveners }
                </tr>
                <tr><td colspan="9">&nbsp;</td></tr>
                <tr>
                    <td colspan="13" valign="bottom" align="left">
<!--                        <input type="submit" class="btn" name="removeRegistrants" value="${ _("remove selected")}">    -->
                    </td>
                </tr>
                </form>
                <tr>
                    <td colspan="9">&nbsp;</td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>