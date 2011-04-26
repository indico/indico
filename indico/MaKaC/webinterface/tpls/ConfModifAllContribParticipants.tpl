<script type="text/javascript">
<!--
function selectAll()
{
if (!document.participantsForm.participants.length)
        {
            document.participantsForm.participants.checked=true
        }else{
for (i = 0; i < document.participantsForm.participants.length; i++)
    {
    document.participantsForm.participants[i].checked=true
    }
}
}

function unselectAll()
{
if (!document.participantsForm.participants.length)
        {
            document.participantsForm.participants.checked=false
        }else{
for (i = 0; i < document.participantsForm.participants.length; i++)
    {
    document.participantsForm.participants[i].checked=false
    }
}
}
//-->
</script>
<table width="100%">
    <tr>
        <td>
            <a name="results"></a>
            <table align="center" width="100%" border="0" style="border-left: 1px solid #777777;" cellpadding="0" cellspacing="0">
                <tr>
                    <td colspan="9" style="background:#E5E5E5; color:gray">

                        <table cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td colspan=2 class="groupTitle" width="100%">&nbsp;&nbsp;&nbsp;${ title } (${ participantNumber })</td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td colspan="9">&nbsp;</td>
                </tr>
                <form action=${ participantSelectionAction } method="post" name="participantsForm">
                <tr>
                    ${ columns }
                    ${ participants }
                </tr>
                <tr><td colspan="9">&nbsp;</td></tr>
                </form>
                <tr>
                    <td colspan="9">&nbsp;</td>
                </tr>
            </table>
        </td>
    </tr>
</table>
