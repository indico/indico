<form method="POST" onsubmit="setPresentersParam(this);" action="${ postURL }">
    ${ locator }
    <table width="60%" cellspacing="0" align="left" border="0" style="padding-left:5px; padding-top:5px;">
        <tr>
            <td colspan="2" class="groupTitle"> ${ _("Creating a new sub contribution (basic data)")}</td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD" style="padding-top:10px;"><span class="titleCellFormat"> ${ _("Title")}</span></td>
            <td bgcolor="white" width="100%" style="padding-top:10px;"><input type="text" name="title" size="65" value="${ title }"></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Description")}</span></td>
            <td bgcolor="white" width="100%"><textarea name="description" cols="65" rows="10" wrap="soft">${ description }</textarea></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Keywords")}<br><small>( ${ _("one per line")})</small></span></td>
            <td bgcolor="white" width="100%"><textarea name="keywords" cols="65" rows="3">${ keywords }</textarea></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Duration")}</span></td>
            <td bgcolor="white" width="100%">
                <input type="text" size="2" name="durationHours" id="durationHours" value="${ durationHours }">:
                <input type="text" size="2" name="durationMinutes" id="durationMinutes" value="${ durationMinutes }">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD" style="padding-bottom:20px; padding-top:10px;"><span class="titleCellFormat"> ${ _("Presenter")}</span></td>
            <td width="100%" style="padding-bottom:20px;">
                <table width="100%" style="padding-top:6px;">
                    <tr>
                        <td id="parentTDPresenters" style="width:79%; display:none"><ul id="inPlacePresenters" class="UIPeopleList"></ul></td>
                        <td nowrap valign="top" style="width: 21%; text-align:left;">
                            <span id="inPlacePresentersMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                                <a class="dropDownMenu fakeLink" onclick="presenterManager.addManagementMenu();">${ _("Add presenter") }</a>
                            </span>
                        </td>
                        <input type="hidden" name="presenters" id="presenters"></input>
                    </tr>
                </table>
            </td>
        </tr>
        <tr align="center">
            <td colspan="2" style="border-top:1px solid #777777;" valign="bottom" align="center">
                <table align="center">
                    <tr>
                        <td><input type="submit" class="btn" value="${ _("ok")}" name="ok" id="okBtn"></td>
                        <td><input type="submit" class="btn" value="${ _("cancel")}" name="cancel"></td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>
<script  type="text/javascript">

        IndicoUI.executeOnLoad(function()
    {
        var parameterManager = new IndicoUtil.parameterManager();
        var submitButton = $E('okBtn');

        submitButton.observeClick(function(){
            if (!parameterManager.check()) {
                return false;
            }
        });

        parameterManager.add($E('durationHours'), 'int', false);
        parameterManager.add($E('durationMinutes'), 'int', false);
    });

var presenterManager = new AddSubContributionPresenterListManager($E('inPlacePresenters'),
        $E('inPlacePresentersMenu'), $E('parentTDPresenters'),  "presenter", ${ authors | n,j }, '${ eventType }');

function setPresentersParam(data) {
    var usersList = presenterManager.getUsersList();
    $E('presenters').set(Json.write(usersList));
    return true;
}

</script>