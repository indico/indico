<%page args="modifying=None, showParent=None, conf=None, event=None, parentRoomInfo=None, eventId=None, parentName=None"/>
<tr>
  <td class="titleCellTD"><span class="titleCellFormat">${ _("Place")}</span></td>
  <td>
      ${ template_hook('event-location-field', event=(event.as_event if event else None)) }
  </td>
</tr>
<script>
    function injectValuesInForm(form, otherActions) {
        form.observeEvent('submit', function() {
            if (otherActions) {
               return otherActions();
            }
      });
    };
</script>
