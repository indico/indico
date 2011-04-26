<td class="ttManagementBlock" style="vertical-align: top; background-color: ${ bgcolor }" rowspan="${ rowspan }" width="${ width }%" ${ colspan } >
<div style="height: 20px; width: 100%;">
  <div style="width: 60px; float: right;" class="nonLinked">
    <div class="ttModifIcon" style="margin: 3px;" onclick="return breakMenu($E(this), '${ modifyAction(self_._breakEntry) }', '${ deleteAction(self_._breakEntry) }', '${ relocateAction(self_._breakEntry, targetDay = self_._breakEntry.getAdjustedStartDate().strftime("%Y-%m-%d")) }')">
    </div>
    <div style="margin-top: 3px;">
      <a href="${ moveUpAction(self_._breakEntry) }"><img src="${ Config.getInstance().getSystemIconURL("upArrow") }" border="0" alt="${ _("move entry before the previous one")}"></a>
      <a href="${ moveDownAction(self_._breakEntry) }"><img src="${ Config.getInstance().getSystemIconURL("downArrow") }" border="0" alt="${ _("move entry after the next one")}"></a>
    </div>
  </div>
</div>
<div style="overflow: show; margin-left: 10px; margin-bottom: 5px;color:${ self_._breakEntry.getTextColor() };">


  <p style="font-size: 12pt; margin-top: 5px; margin-bottom: 2px;
        % if self_._breakEntry.isTextColorToLinks():
            color:${ self_._breakEntry.getTextColor() };
        % endif
">
    <%from MaKaC.common.TemplateExec import truncateTitle %>
    ${ self_.htmlText(truncateTitle(self_._breakEntry.getTitle(), 40)) }
  </p>
  <small class="ttMBlockExtraInfo">
    % if self_._breakEntry.getRoom() != None:
    ${ "%s: "%self_._breakEntry.getRoom().getName() }
    % endif
    ${ self_.htmlText(self_._breakEntry.getAdjustedStartDate().strftime("%H:%M")) }-${ self_.htmlText(self_._breakEntry.getAdjustedEndDate().strftime("%H:%M")) }
  </small>

</div>
</td>
