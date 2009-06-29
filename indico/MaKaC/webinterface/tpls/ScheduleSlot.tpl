<td class="ttSessionManagementBlock" onclick="if(validClick(this, event)) { window.location = '<%= "%s#slot%s" % (str(urlHandlers.UHSessionModifSchedule.getURL(self._slot.getSession())),self._slot.getId()) %>';} return true;" style="vertical-align: top; background-color: <%= bgcolor %>" rowspan="<%= rowspan %>" width="<%= width %>%%" <%= colspan %> >

<% modifURL = urlHandlers.UHConfModSchEditSlot.getURL(self._slot) %>
  <% if not self._conf.getEnableSessionSlots() : %>
  <% modifURL.addParam("hideSlot",1) %>
<% end %>

<% delURL = urlHandlers.UHConfModSlotRem.getURL(self._slot) %>
<% if len(self._slot.getSession().getSlotList()) <= 1: %>
   <% delURL=urlHandlers.UHConfModSessionRem.getURL(self._slot.getSession()) %>
<% end %>

<div style="height: 20px; width: 100%%;">
  <div style="width: 60px; float: right;" class="nonLinked">
    <div class="ttModifIcon" style="margin: 3px;" onclick="return sessionMenu($E(this), '<%= urlHandlers.UHSessionModification.getURL(self._slot.getSession()) %>', '<%= self._conf.id %>', '<%= self._slot.getSession().id %>', '<%= "%s#slot%s" % (str(urlHandlers.UHSessionModifSchedule.getURL(self._slot.getSession())),self._slot.getId()) %>');">
    </div>
    <div style="margin-top: 3px;">
      <a href="<%= urlHandlers.UHConfModScheduleMoveEntryUp.getURL(self._slot.getConfSchEntry()) %>"><img src="<%= systemIcon("upArrow") %>" border="0" alt="<%= _("move entry before the previous one")%>"></a>
      <a href="<%= urlHandlers.UHConfModScheduleMoveEntryDown.getURL(self._slot.getConfSchEntry()) %>"><img src="<%= systemIcon("downArrow") %>" border="0" alt="<%= _("move entry after the next one")%>"></a>
    </div>
  </div>
</div>

<div style="overflow: show; margin-left: 10px; margin-bottom: 5px; color:<%= self._slot.getSession().getTextColor() %>;">
  <p style="font-size: 12pt; margin-top: 5px; margin-bottom: 2px; 
	    <% if self._slot.getSession().isTextColorToLinks(): %>
              <%= "color:%s;" % self._slot.getSession().getTextColor() %>
	    <% end %>">
	<%from MaKaC.common.TemplateExec import truncateTitle %>    
    <% if self._conf.getEnableSessionSlots() and self._slot.getTitle().strip() != "": %>
      <%= "%s: %s"%(self.htmlText(truncateTitle(self._slot.getSession().getTitle(), 40)), self.htmlText(self._slot.getTitle())) %>
    <% end %>
    <% else: %>
      <%= self.htmlText(truncateTitle(self._slot.getSession().getTitle(), 40)) %>
    <% end %>
  </p>
  <small class="ttMBlockExtraInfo">
        <% if self._slot.getRoom() is not None and self._slot.getRoom().getName().strip()!="": %>
          <%= self.htmlText("%s: " % self._slot.getRoom().getName()) %>
	<% end %> 
	<%= self.htmlText(self._slot.getAdjustedStartDate().strftime("%H:%M")) %>-<%= self.htmlText(self._slot.getAdjustedEndDate().strftime("%H:%M")) %></small>

  <% if self._slot.getSession().isClosed(): %>
    <strong>[ <a href="<%= urlHandlers.UHSessionOpen.getURL(self._slot.getSession()) %>"><%= _("reopen session")%></a> ]</strong>
  <% end %>
</div>

</td>