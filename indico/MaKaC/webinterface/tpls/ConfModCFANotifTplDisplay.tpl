<table width="90%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Name")}</span></td>
        <td bgcolor="white" width="100%"><b>${ name }</b></td>
        <td valign="bottom" rowspan="7" bgcolor="white" width="100%">
            <form action=${ modifDataURL } method="POST">
                <div style="text-align:right;">
                    <input type="submit" class="btn" value="${ _("Modify")}">
                </div>
            </form>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Description")}</span></td>
        <td bgcolor="white" width="100%"><b>${ description }</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("From")}</span></td>
        <td bgcolor="white" width="100%"><b>${ From }</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("To addresses")}</span></td>
        <td bgcolor="white" width="100%"><b>${ toAddrs }</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Cc addresses")}</span></td>
        <td bgcolor="white" width="100%"><b>${ CCAddrs }</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Subject")}</span></td>
        <td bgcolor="white" width="100%"><b>${ subject }</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Body")}</span></td>
        <td bgcolor="white" width="100%"><pre>${ body }</pre></td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Conditions")}</span></td>
        <td width="100%" colspan="2">
            <table width="100%">
                <tr>
                    <form action=${ remConditionsURL } method="POST">
                    <td width="100%" valign="top" style="min-width:145px;">
                            ${ conditions }
                    </td>
                    <input type="hidden" value="" name="selCond">
                    </form>
                    <td id="createConditionCell" align="right" valign="top">
                        <input id="createConditionButton" type="submit" class="btn" value="${ _("Add new condition")}">
                    </td>
                    <td id="createConditionDisplay" align="right" valign="top" valign="bottom" nowrap style="padding-bottom:10px; display:none;">
                        <div class="shadowRectangle" style="padding-right:15px;">
                        <table>
                            <form action=${ newConditionURL } method="POST">
                            <tr>
                                <td colspan="2" style="text-align:center; padding-bottom:5px;">
                                    <span class="groupTitleSmallPaper" style="border:0px; font-size:13px;">${ _("Choose the condition that triggers the email")}</span>
                                </td>
                            </tr>
                            <tr>
                                <td nowrap class="titleCellTD" style="padding-top:5px; width:70%;">
                                    <span class="titleCellFormat"> ${ _("The email will be sent when the abstract is") }</span>
                                </td>
                                <td><select id="condTypeSelect" name="condType" onchange="checkSelectCondition();">${ availableConditions }</select></td>
                            </tr>
                            <tr id="contribTypeSelect">
                                <td nowrap class="titleCellTDSecondLevel" style="padding-top:3px;"><span> ${ _("and the contribution type is") }</span></td>
                                <td style="padding-top:3px;">
                                    <select name="contribType">
                                        <option value="--any--">${ _("--any--") }</option>
                                        <option value="--none--">${ _("--none--") }</option>
                                        % for ct in contribTypeList:
                                            <option value=${ quoteattr(ct.getId()) }> ${ ct.getName() } </option>
                                        % endfor
                                    </select>
                                </td>
                            </tr>
                            <tr id="trackSelect">
                                <td nowrap class="titleCellTDSecondLevel" style="padding-top:3px;"><span> ${ _("and the track is") }</span></td>
                                <td style="padding-top:3px;">
                                    <select name="track">
                                        <option value="--any--">${ _("--any--") }</option>
                                        <option value="--none--">${ _("--none--") }</option>
                                        % for track in trackList:
                                            <option value=${ quoteattr(track.getId()) }> ${ track.getTitle() } </option>
                                        % endfor
                                    </select>
                                </td>
                            </tr>
                            <tr>
                                <td></td>
                                <td align="left" style="padding-top:5px;">
                                    <input id="createButton" type="submit" class="btn" value="${ _("Create")}">
                                    <button id="cancelButton"  type="button">${ _("Cancel")}</button>
                                </td>
                            </tr>
                            </form>
                        </table>
                        </div>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>

<script type="text/javascript">

$E('createConditionButton').observeClick(function() {
	$E('createConditionCell').dom.style.display = 'none';
    $E('createConditionDisplay').dom.style.display = '';
});

$E('cancelButton').observeClick(function() {
    $E('createConditionDisplay').dom.style.display = 'none';
    $E('createConditionCell').dom.style.display = '';
});

function checkSelectCondition() {
    if ($E('condTypeSelect').dom.value != 'accepted') {
        $E('contribTypeSelect').dom.style.display = 'none';
        $E('trackSelect').dom.style.display = 'none';
    } else {
        $E('contribTypeSelect').dom.style.display = '';
        $E('trackSelect').dom.style.display = '';
    }
}

checkSelectCondition();

</script>
