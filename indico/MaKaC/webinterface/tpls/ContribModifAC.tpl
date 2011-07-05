<table width="100%" class="ACtab"><tr><td>
<br>
${ modifyControlFrame }
<br>
${ accessControlFrame }
<br>
<table class="groupTable">
    <tr>
        <td colspan="3"><div class="groupTitle">${ _("Submission control")}</div></td>
    </tr>
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat">${ _("Submitters")}<br><font size="-2">(${ _("users allowed to submit material for this contribution")})</font></span></td>
        <td width="100%" style="padding-bottom:20px;">
            <table width="100%" style="padding-top:6px;">
                <tr>
                    <td id="parentTDSubmitters" style="width:79%; display:none"><ul id="inPlaceSubmitters" class="UIPeopleList"></ul></td>
                </tr>
                <tr>
                    <td nowrap valign="top" style="width: 21%; text-align:left;">
                        <input type="button" value='${ _("Add submitter") }' onclick="submitterManager.addExistingUser();">
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>
</tr></td></table>


<script>

var submitterManager = new SubmissionControlListManager('${ confId }', '${ contribId }', $E('inPlaceSubmitters'),
        $E('parentTDSubmitters'),  "submitter", '${ eventType }');

</script>
