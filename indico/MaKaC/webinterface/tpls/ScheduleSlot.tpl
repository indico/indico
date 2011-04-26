<td class="ttSessionManagementBlock" onclick="if(validClick(this, event)) { window.location = '${ "%s#slot%s" % (str(urlHandlers.UHSessionModifSchedule.getURL(self_._slot.getSession())),self_._slot.getId()) }';} return true;" style="vertical-align: top; background-color: ${ bgcolor }" rowspan="${ rowspan }" width="${ width }%" ${ colspan } >

<% modifURL = urlHandlers.UHConfModSchEditSlot.getURL(self_._slot) %>
  % if not self_._conf.getEnableSessionSlots() :
  <% modifURL.addParam("hideSlot",1) %>
% endif

<% delURL = urlHandlers.UHConfModSlotRem.getURL(self_._slot) %>
% if len(self_._slot.getSession().getSlotList()) <= 1:
   <% delURL=urlHandlers.UHConfModSessionRem.getURL(self_._slot.getSession()) %>
% endif


<div style="height: 20px; width: 100%;">
  <div style="width: 60px; float: right;" class="nonLinked">
    <div class="ttModifIcon" style="margin: 3px;" onclick="return sessionMenu($E(this), '${ urlHandlers.UHSessionModification.getURL(self_._slot.getSession()) }', '${ self_._conf.id }', '${ self_._slot.getSession().id }', '${ "%s#slot%s" % (str(urlHandlers.UHSessionModifSchedule.getURL(self_._slot.getSession())),self_._slot.getId()) }');">
    </div>
    <div style="margin-top: 3px;">
      <a href="${ urlHandlers.UHConfModScheduleMoveEntryUp.getURL(self_._slot.getConfSchEntry()) }"><img src="${ systemIcon("upArrow") }" border="0" alt="${ _("move entry before the previous one")}"></a>
      <a href="${ urlHandlers.UHConfModScheduleMoveEntryDown.getURL(self_._slot.getConfSchEntry()) }"><img src="${ systemIcon("downArrow") }" border="0" alt="${ _("move entry after the next one")}"></a>
    </div>
  </div>
</div>

<div style="overflow: show; margin-left: 10px; margin-bottom: 5px; color:${ self_._slot.getSession().getTextColor() };">
  <p style="font-size: 12pt; margin-top: 5px; margin-bottom: 2px;
        % if self_._slot.getSession().isTextColorToLinks():
              ${ "color:%s;" % self_._slot.getSession().getTextColor() }
        % endif
">
    <%from MaKaC.common.TemplateExec import truncateTitle %>
    % if self_._conf.getEnableSessionSlots() and self_._slot.getTitle() and self_._slot.getTitle().strip() != "":
      ${ "%s: %s"%(self_.htmlText(truncateTitle(self_._slot.getSession().getTitle(), 40)), self_.htmlText(self_._slot.getTitle())) }
    % else:
      ${ self_.htmlText(truncateTitle(self_._slot.getSession().getTitle(), 40)) }
    % endif
  </p>
  <small class="ttMBlockExtraInfo">
        % if (self_._slot.getRoom() is not None) and (self_._slot.getRoom().getName() != None) and (self_._slot.getRoom().getName().strip()!=""):
          ${ self_.htmlText("%s: " % self_._slot.getRoom().getName()) }
    % endif
    ${ self_.htmlText(self_._slot.getAdjustedStartDate().strftime("%H:%M")) }-${ self_.htmlText(self_._slot.getAdjustedEndDate().strftime("%H:%M")) }</small>
  % if self_._slot.getSession().isClosed():
    <strong>[ <a href="${ urlHandlers.UHSessionOpen.getURL(self_._slot.getSession()) }">${ _("reopen session")}</a> ]</strong>
  % endif
</div>

</td>
