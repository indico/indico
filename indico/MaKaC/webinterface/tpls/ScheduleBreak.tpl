<td class="ttManagementBlock" style="vertical-align: top; background-color: <%= bgcolor %>" rowspan="<%= rowspan %>" width="<%= width %>%%" <%= colspan %> >
<div style="height: 20px; width: 100%;">
  <div style="width: 60px; float: right;" class="nonLinked">
    <div class="ttModifIcon" style="margin: 3px;" onclick="return breakMenu($E(this), '<%= modifyAction(self._breakEntry) %>', '<%= deleteAction(self._breakEntry) %>', '<%= relocateAction(self._breakEntry, targetDay = self._breakEntry.getAdjustedStartDate().strftime("%Y-%m-%d")) %>')">
    </div>
    <div style="margin-top: 3px;">
      <a href="<%= moveUpAction(self._breakEntry) %>"><img src="<%= Config.getInstance().getSystemIconURL("upArrow") %>" border="0" alt="<%= _("move entry before the previous one")%>"></a>
      <a href="<%= moveDownAction(self._breakEntry) %>"><img src="<%= Config.getInstance().getSystemIconURL("downArrow") %>" border="0" alt="<%= _("move entry after the next one")%>"></a>
    </div>
  </div>
</div>
<div style="overflow: show; margin-left: 10px; margin-bottom: 5px;color:<%= self._breakEntry.getTextColor() %>;">


  <p style="font-size: 12pt; margin-top: 5px; margin-bottom: 2px;
	    <% if self._breakEntry.isTextColorToLinks(): %>
            color:<%= self._breakEntry.getTextColor() %>;
	    <% end %>">
	<%from MaKaC.common.TemplateExec import truncateTitle %>
    <%= self.htmlText(truncateTitle(self._breakEntry.getTitle(), 40)) %>
  </p>
  <small class="ttMBlockExtraInfo">
    <% if self._breakEntry.getRoom() != None: %>
    <%= "%s: "%self._breakEntry.getRoom().getName() %>
    <% end %>
    <%= self.htmlText(self._breakEntry.getAdjustedStartDate().strftime("%H:%M")) %>-<%= self.htmlText(self._breakEntry.getAdjustedEndDate().strftime("%H:%M")) %>
  </small>

</div>
</td>