<% import MaKaC %>

<tr>
  <td class="titleCellTD"><span class="titleCellFormat"><%= _("Place")%></span></td>

  <td>
    <div id ="roomChooser"></div>
  </td>
</tr>


<script type="text/javascript">

  <% if modifying: %>
    var info = $O(<%= jsonEncode(roomInfo(event, level='own')) %>);
  <% end %>
  <% else: %>
    var info = $O();
  <% end %>

  var parentEvt = 
  <% if showParent: %>
    $O(<%= jsonEncode(parentRoomInfo) %>)
  <% end %>
  <% else: %>
    false
  <% end %>;

  IndicoUI.executeOnLoad(function() {

  <% if self._rh._target and not isinstance(self._rh._target, MaKaC.conference.Category): %>
    <% eventFavorites = self._rh._target.getConference().getId() %>
  <% end %>
  <% else: %>
    <% eventFavorites = 'false' %>
  <% end %>
  
  var rbWidget = new RoomBookingWidget(info, parentEvt, <%= jsBoolean(not modifying) %>, <%= eventFavorites %>);

  var domContent = rbWidget.draw();

  $E('roomChooser').set(domContent);

  });

  function injectValuesInForm(form, otherActions) {

     form.observeEvent('submit', function() {
        each({'room': 'roomName','location': 'locationName', 'address': 'locationAddress'}, 
             function(val, key) {
	       // prevent problem with back button
	       var input = $E('jsGenerated_'+key) || Html.input('hidden', {id: 'jsGenerated_'+key, name: val});
	       input.set(info.get(key));
	       form.append(input);
	     });
	if (otherActions) {
	   return otherActions();
	}
      });
    
    };


</script>
