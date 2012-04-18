<%page args="modifying=None, showParent=None, conf=None, event=None, parentRoomInfo=None, eventId=None, parentName=None"/>
<% import MaKaC %>
<% from indico.util import json %>

<tr>
  <td class="titleCellTD"><span class="titleCellFormat">${ _("Place")}</span></td>

  <td>
    <div id ="roomChooser"></div>
  </td>
</tr>


<script type="text/javascript">

  % if modifying:
    var info = $O(${ jsonEncode(roomInfo(event, level='own')) });
  % else:
    var info = $O();
  % endif

  % if showParent:
    var parentEvt = $O(${ jsonEncode(parentRoomInfo) });
    var parentName = ${ jsonEncode(parentName) };
  % else:
    var parentEvt = false;
    var parentName = null;
  % endif
;

  IndicoUI.executeOnLoad(function() {

  % if self_._rh._target and not isinstance(self_._rh._target, MaKaC.conference.Category):
    <% eventFavorites = self_._rh._target.getConference().getFavoriteRooms() %>
  % else:
    <% eventFavorites = [] %>
  % endif

  % if conf:
      var ttdata = ${ MaKaC.schedule.ScheduleToJson.process(conf.getSchedule(), conf.getTimezone(), None,
                                                                                days = None, mgmtMode = True) | n,j } ;
      <% from MaKaC.common.Conversion import Conversion %>
      var bookedRooms = ${ json.dumps(Conversion.reservationsList(conf.getRoomBookingList())) };
      rbWidget = new RoomBookingReservationWidget(Indico.Data.Locations, info, parentEvt, nullRoomInfo(info), ${ eventFavorites }, ${"null" if modifying else "Indico.Data.DefaultLocation"}, bookedRooms, ttdata, null, "${ eventId }", parentName);
  % else:
      rbWidget = new RoomBookingWidget(Indico.Data.Locations, info, parentEvt, nullRoomInfo(info), ${ eventFavorites }, ${"null" if modifying else "Indico.Data.DefaultLocation"}, parentName);
  % endif

  var domContent = rbWidget.draw();

  $E('roomChooser').set(domContent);

  rbWidget.postDraw();

  });

  function injectValuesInForm(form, otherActions) {

     form.observeEvent('submit', function() {
        each({'room': 'roomName','location': 'locationName', 'address': 'locationAddress'},
             function(val, key) {
           // prevent problem with back button
           var input = $E('jsGenerated_'+key) || Html.input('hidden', {id: 'jsGenerated_'+key, name: val});
           if (info.get(key) != null) {
               input.set(info.get(key));
               form.append(input);
           }
         });
    if (otherActions) {
       return otherActions();
    }
      });

    };


</script>
