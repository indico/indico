<tr>
    <td class="titleCellTD" nowrap>
        <span class="titleCellFormat">${ _("Sync with my Outlook calendar")}</span>
    </td>
    <td class="blacktext spaceLeft" nowrap><span id="tabShowOutlookEvents"></span>
    <span style="color: #aaa; size: 10px;">(${ _("Add Indico events in which I participate to my Outlook calendar")})</span></td>
    <script type="text/javascript">
        $E("tabShowOutlookEvents").set(new RemoteSwitchButton(${"true" if outlookPluginEnabled else "false"},
                Html.img({src:imageSrc("tick.png")}), Html.img({src:imageSrc("cross.png")}), "user.hideOutlookEvents", "user.showOutlookEvents",{"userId": "${userId}"}).draw());
    </script>
<tr>
