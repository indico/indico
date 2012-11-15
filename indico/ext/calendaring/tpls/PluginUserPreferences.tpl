<tr>
    <td class="titleCellTD"><span class="titleCellFormat">
        ${ _("Add events in which I participate to outlook calendar")}</span>
    </td>
    <td class="blacktext spaceLeft" nowrap><div id="tabShowOutlookEvents"></div></td>
    <script type="text/javascript">
        $E("tabShowOutlookEvents").set(new RemoteSwitchButton(${"true" if outlookPluginEnabled else "false"},
                Html.img({src:imageSrc("tick.png")}), Html.img({src:imageSrc("cross.png")}), "user.hideOutlookEvents", "user.showOutlookEvents",{"userId": "${userId}"}).draw());
    </script>
<tr>
