<%! 
declareTemplate(newTemplateStyle=True)
location = self._conf.getLocation()
room = self._conf.getRoom()

if location:
    locationName = location.getName()
    address = self._conf.getLocation().getAddress().replace('\r\n','\\n').replace('\n','\\n')
else:
    locationName = 'None'
    address = ''

if room:
    roomName = room.name
else:
    roomName = 'None'

%>

<table style="width: 80%; margin: auto; margin-bottom: 20px;">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Start date")%></span></td>
        <td class="blacktext"><%= start_date %></td>
        <form action=<%= editURL %> method="POST">
        <td rowspan="2" ><input type="submit" class="btn" value="<%= _("modify")%>"></td>
        </form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("End date")%></span></td>
        <td bgcolor="white" class="blacktext"><%= end_date %></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Options")%></span></td>
        <td><div id="autoSolveConflictPlace">
                <span id="autoSolveConflictButton">                    
                </span>
            </div>
            <div id="sessionsPlace">
                <span id="sessionsButton">                    
                </span>
            </div>
            <div id="sessionSlotsPlace">
                <span id="sessionSlotsButton">                    
                </span>
            </div>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Timezone") %></span></td>
        <td bgcolor="white" class="blacktext"><%= timezone %></td>
    </tr>
</table>

    <div style="overflow: auto; padding: 10px; auto; margin-right: auto; margin-left: auto; margin-bottom: 10px; margin-top: 15px;">

        <span style="margin-right: 5px;" class="dataCaptionFormat"><%= _("Show") %>:</span>
        <form action="<%= urlHandlers.UHConfModifSchedule.getURL(self._conf) %>" method="GET" style="display: inline">
          <select name="day" onchange="javascript: this.form.submit();">
            <% for n in range(len(dayList)): %>
            <option value="<%= n %>"                        
                    <% if len(self._dayList) == 1 and dayList[n] in self._dayList: %>
                    selected
                    <% end %>>
              <%= dayList[n].getDate().strftime("%A, %d %B %Y") %>                             
            </option>
            <% end %>
            <option value="all" 
              <% if len(self._dayList) > 1: %>           
              selected
              <% end %>>All days</option>
          </select>
          <input type="hidden" name="confId" value="<%= self._conf.id %>" />
        </form>          

      <% if self.addControlsEnabled(): %>
	<a href="#" style="margin-left: 15px; margin-right: 8px;" id="addLink" class="dropDownMenu highlight">add</a> <span style="color: #AAAAAA;">|</span> 
        <a href="<%= urlHandlers.UHConfModifReschedule.getURL(self._conf, targetDay=dayDate.strftime("%Y-%m-%d")) %>" style="margin-left: 8px;">reschedule</a> 
      
      <% end %>
      <% else: %>

      <a href="<%= urlHandlers.UHConfModifSchedule.getURL(self._conf, day = days) %>" style="margin-left: 20px;"><%= _("go to timetable")%></a>
      <% end %>

    </div>      

    <%= content %>

<script type="text/javascript">
$E('autoSolveConflictButton').set(IndicoUI.Widgets.Generic.switchOptionButton('schedule.setTimeConflictSolving', 
                                            {conference: '<%= self._conf.id %>'}, 
                                            'Automatically solve timing conflicts'
));
$E('sessionsButton').set(IndicoUI.Widgets.Generic.switchOptionButton('schedule.setScheduleSessions', 
                                            {conference: '<%= self._conf.id %>'}, 
                                            'Sessions',
                                            true
));
$E('sessionSlotsButton').set(IndicoUI.Widgets.Generic.switchOptionButton('schedule.setSessionSlots', 
                                            {conference: '<%= self._conf.id %>'}, 
                                            'Session Slots',
                                            true
));

var parentEventRoomData = $O(<%= jsonEncode(roomInfo(self._rh._target)) %>);

var addSession = curry(IndicoUI.Dialogs.addSession, 
    'schedule.event.addSession',
    'schedule.event.getDayEndDate',
    <%= jsonEncode({'conference': self._conf.id }) %>, 
    <%= jsonEncode({'location': locationName,
    'room': roomName,
    'address': address }) %>,
    parentEventRoomData,
    '<%= dayDate.strftime("%d/%m/%Y") %>',
    <%= jsBoolean(rbActive) %>
    );

var addContribution = function() {
    var dialog = new AddContributionDialog(<%= map(lambda x: x.getDate().strftime("%d/%m/%Y"), dayList) %>,
					   <%= map(lambda x: x.getDate().strftime("%d/%m/%Y"), self._dayList) %>,
					   'schedule.event.addContribution',
                                           'schedule.event.getDayEndDate',
					   <%= jsonEncode({'conference': self._conf.id }) %>, 
					   <%= jsonEncode({'location': locationName,
					   'room': roomName,
					   'address': address }) %>,
					   parentEventRoomData,
					   '<%= self._conf.getStartDate().strftime("%d/%m/%Y %H:%M") %>',
					   '<%= dayDate.strftime("%d/%m/%Y") %>',
					   <%= jsBoolean(rbActive) %>,
					   <%= jsBoolean(self._conf.getType() != 'meeting') %>
					   );

    dialog.execute();
};

var addBreak = curry(IndicoUI.Dialogs.addBreak, 
    'schedule.event.addBreak',
    'schedule.event.getDayEndDate',
    <%= jsonEncode({'conference': self._conf.id }) %>, 
    <%= jsonEncode({'location': locationName,
    'room': roomName,
    'address': address }) %>,
    parentEventRoomData,
    '<%= self._conf.getStartDate().strftime("%d/%m/%Y %H:%M") %>',
    '<%= dayDate.strftime("%d/%m/%Y") %>',
    <%= jsBoolean(rbActive) %>
    );

<% if self.addControlsEnabled(): %>
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
    <% if self._conf.getEnableSessions(): %>
      menuItems['<%= _("Session") %>'] = addSession;
    <% end %>
    menuItems['<%= _("Contribution") %>'] = addContribution;
    menuItems['<%= _("Break") %>'] = addBreak;

    manageMenu = new PopupMenu(menuItems, [addLink], 'categoryDisplayPopupList');
    var pos = addLink.getAbsolutePosition();
    manageMenu.open(pos.x - 5, pos.y + addLink.dom.offsetHeight + 2);
    return false;
});
<% end %>

var breakMenu = function(link, editURL, deleteURL, relocateURL) {
 
    var manageBreakMenu = null;
    // Close the menu if clicking the link when menu is open
    if (manageBreakMenu && manageBreakMenu.isOpen()) {
        manageBreakMenu.close();
        manageBreakMenu = null;
        return;
    }
    var menuItems = {};
    menuItems['<%= _("Edit") %>'] = editURL;
    menuItems['<%= _("Delete") %>'] = function() { 
                                          if (confirm("<%= _("Are you sure you want to delete this break?") %>")) {
       					    window.location = deleteURL;
					  }
					  return false;
				      };
    menuItems['<%= _("Relocate") %>'] = relocateURL;

    manageBreakMenu = new PopupMenu(menuItems, [link], 'categoryDisplayPopupList', true, true);
    var pos = link.getAbsolutePosition();

    manageBreakMenu.open(pos.x + 15, pos.y + link.dom.offsetHeight + 2);
    return false;
    }

var contributionMenu = function(link, editURL, contributionId, conferenceId, deleteURL, relocateURL) {
 
    var manageContribMenu = null;
    // Close the menu if clicking the link when menu is open
    if (manageContribMenu && manageContribMenu.isOpen()) {
        manageContribMenu.close();
        manageContribMenu = null;
        return;
    }
    var menuItems = {};
    menuItems['<%= _("Edit") %>'] = editURL;
    menuItems['<%= _("Add Subcontribution") %>'] = function() {
                        IndicoUI.Dialogs.addSubContribution(contributionId, conferenceId);
			return false;
			}
    menuItems['<%= _("Delete") %>'] = function() {
                                         if (confirm('<%= _("Are you sure you want to delete this contribution")%> ?')) {
					 window.location = deleteURL;
                                  }
    };
    menuItems['<%= _("Relocate") %>'] = relocateURL;

    manageContribMenu = new PopupMenu(menuItems, [link], 'categoryDisplayPopupList', true, true);
    var pos = link.getAbsolutePosition();

    manageContribMenu.open(pos.x + 15, pos.y + link.dom.offsetHeight + 2);
    return false;
    }

var sessionMenu = function(link, editURL, confId, sessionId, timetableURL) {
 
    var manageSessionMenu = null;
    // Close the menu if clicking the link when menu is open
    if (manageSessionMenu && manageSessionMenu.isOpen()) {
        manageSessionMenu.close();
        manageSessionMenu = null;
        return;
    }
    var menuItems = {};
    menuItems['<%= _("Edit") %>'] = editURL;
    menuItems['<%= _("Delete") %>'] = function() {
                                         if (confirm('<%= _("Are you sure you want to delete this session?")%> ?')) {
					 IndicoUI.Services.deleteSession(confId, sessionId);
                                  }
    };
    menuItems['<%= _("View timetable") %>'] = timetableURL;

    manageSessionMenu = new PopupMenu(menuItems, [link], 'categoryDisplayPopupList', true, true);
    var pos = link.getAbsolutePosition();

    manageSessionMenu.open(pos.x + 15, pos.y + link.dom.offsetHeight + 2);
    return false;
    }

function validClick(element, event)
/* Checks if the button area was clicked */
{
      return !($E(element).getElementsByClassName('nonLinked')[0].ancestorOf($E(eventTarget(event))));
}

// Add highlight effect

each($E(document).getElementsByClassName('ttSessionManagementBlock'),
     function(elem) {
        highlightWithMouse(elem, elem);
     });

</script>

