<%! 
declareTemplate(newTemplateStyle=True)

import MaKaC

#############################################
sessionRoom = sessionList[session].getRoom()
sessionLocation = sessionList[session].getLocation()

if sessionRoom:
    sessionRoomName = sessionRoom.name
else:
    sessionRoomName = 'None'

if sessionLocation:
    sessionLocationName = sessionLocation.getName()
    sessionAddress = sessionLocation.getAddress().replace('\r\n','\\n').replace('\n','\\n')
else:
    sessionLocationName = 'None'
    sessionAddress = ''
##############################################
slotRoom = slot.getRoom()
if slotRoom:
    slotRoomName = slotRoom.name
else:
    slotRoomName = ''
##############################################

%>

<div style="overflow: auto; padding: 10px; margin-left: auto; margin-right: auto;">
  
  <span style="margin-right: 5px;" class="dataCaptionFormat"><%= _("Session") %>:</span>
  <form action="#" method="GET" style="display: inline;">
    <select name="sessionId" onchange="javascript: this.form.submit();">
      <% for key in sessionList: %>
      <option value="<%= key %>"
        <% if key == session: %>
        selected
        <% end %>>
        <%= sessionList[key].getTitle() %>                             
      </option>
      <% end %>
    </select>
    <input type="hidden" name="confId" value="<%= self._conf.id %>" />
  </form>          

<% if self._conf.getEnableSessionSlots(): %>
  <span style="margin-right: 5px; margin-left: 10px;" class="dataCaptionFormat"><%= ("Slot") %>:</span>
  <form action="#" method="GET" style="display: inline;">
    <select name="slot" onchange="javascript: this.form.submit();">               
      <% for key in slotList: %>			        
      <option value="<%= key %>"
        <% if slotList[key] == slot: %>					   
        selected
        <% end %>>
        <%= slotList[key].getTitle() %> (<%= slotList[key].getName() %>)                          
      </option>
      <% end %>
    </select>
    <input type="hidden" name="confId" value="<%= self._conf.id %>" />
    <input type="hidden" name="sessionId" value="<%= session %>" />
  </form>          


  <a href="#" style="margin-left: 20px;" onclick="addSessionSlot(); return false;">add a new slot</a>
<% end %>
</div>                  

<div style="margin: 10px; margin-top: 20px;">

  <ul class="slotHorizontalMenu" style="float:right; color: #AAAAAA;">
    <% if self._conf.getEnableSessionSlots(): %>        
    <li><a href="<%= urlHandlers.UHSessionModSlotEdit.getURL(slot) %>">edit</a></li>
    <% end %>
    |
    <li><a href="#" style="margin-left: 5px;" id="addLink" class="dropDownMenu highlight">add</a></li>
    |
    <li><a href="<%= urlHandlers.UHSessionModSlotCalc.getURL(slot) %>">reschedule</a></li>
  </ul>
  <div>
    <div class="timetableHeader" style="margin-bottom: 15px;"><% if self._conf.getEnableSessionSlots(): %>
    <%=slot.getSession().getTitle() %>: <%= slot.getTitle() %> (<%= slot.getName() %>)
    <% end %>
    <% else: %>
    <%=slot.getSession().getTitle() %>
    <% end %>

    <div style="font-size: 12pt; margin-top: 5px;">
      <span>
	<%= slot.getAdjustedStartDate().strftime("%d %b") %>  
      </span>
      <span>
	<%= slot.getAdjustedStartDate().strftime("%H:%M") %> - <%= slot.getAdjustedEndDate().strftime("%H:%M") %>
      </span>
      <% if slotRoomName: %>
      <span>
	(<%= slotRoomName %>)
      </span>
      <% end %>
    </div>
   </div>
  </div>
  <table style="width:80%;  margin-left: auto; margin-right: auto;">
    <%= slots %>
  </table>
</div>


<script type="text/javascript">

<% if isinstance(self._rh._target, MaKaC.conference.Session): %>
var parentSessionData = $O(<%= jsonEncode(roomInfo(self._rh._target)) %>);
<% end %>
<% else: %>
var parentSessionData = $O(<%= jsonEncode(roomInfo(self._rh._target.getSessionById(session))) %>);
<% end %>

<% if self._conf.getEnableSessionSlots(): %>
var parentRoomData = $O(<%= jsonEncode(roomInfo(slot)) %>);
<% end %>
<% else: %>
var parentRoomData = parentSessionData;
<% end %>


  var addSessionContribution = function() {
    var dialog = new AddContributionDialog(<%= [slot.getAdjustedStartDate().strftime("%d/%m/%Y")] %>,
					   <%= [slot.getAdjustedStartDate().strftime("%d/%m/%Y")] %>,
					   'schedule.slot.addContribution',
                                           'schedule.slot.getDayEndDate',
					   <%= jsonEncode({'conference': self._conf.id, 'session': session, 'slot': slot.id }) %>, 
					   <%= jsonEncode({'location': sessionLocationName,
					   'room': sessionRoomName,
					   'address': sessionAddress }) %>,
					   parentRoomData,
					   '<%= sessionList[session].getAdjustedStartDate().strftime("%d/%m/%Y %H:%M") %>',
					   '<%= dayDate.strftime("%d/%m/%Y") %>',
					   <%= jsBoolean(rbActive) %>,
					   <%= jsBoolean(self._conf.getType() != 'meeting') %>);
    dialog.execute();
  }

  var addSessionSlot = curry(IndicoUI.Dialogs.addSessionSlot, 
      'schedule.session.addSlot',
      'schedule.session.getDayEndDate',
      <%= jsonEncode({'conference': self._conf.id, 'session': session }) %>, 
      <%= jsonEncode({'location': sessionLocationName,
      'room': sessionRoomName,
      'address': sessionAddress }) %>,
      parentSessionData,
      '<%= sessionList[session].getAdjustedStartDate().strftime("%d/%m/%Y %H:%M") %>',
      '<%= dayDate.strftime("%d/%m/%Y") %>',
      <%= jsBoolean(rbActive) %>);

  var addSessionBreak = curry(IndicoUI.Dialogs.addBreak, 
      'schedule.slot.addBreak',
      'schedule.slot.getDayEndDate',
      <%= jsonEncode({'conference': self._conf.id, 'session': session, 'slot': slot.id }) %>, 
      <%= jsonEncode({'location': sessionLocationName,
      'room': sessionRoomName,
      'address': sessionAddress }) %>,
      parentRoomData,
      '<%= sessionList[session].getAdjustedStartDate().strftime("%d/%m/%Y %H:%M") %>',
      '<%= dayDate.strftime("%d/%m/%Y") %>',
       <%= jsBoolean(rbActive) %>
      );

var addLink = $E('addLink');
var manageMenu = null;
addLink.observeClick(function(e) {
    // Close the menu if clicking the link when menu is open
    if (manageMenu != null && manageMenu.isOpen()) {
        manageMenu.close();
        manageMenu = null;
        return;
    }
    var menuItems = {};
    menuItems['<%= _("Contribution") %>'] = addSessionContribution;
    menuItems['<%= _("Break") %>'] = addSessionBreak;

    manageMenu = new PopupMenu(menuItems, [addLink], 'categoryDisplayPopupList');
    var pos = addLink.getAbsolutePosition();
    manageMenu.open(pos.x - 5, pos.y + addLink.dom.offsetHeight + 2);
    return false;
});

</script>

