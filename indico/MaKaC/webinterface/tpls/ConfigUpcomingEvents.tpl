<table>
  <tr>
    <td class="titleCellTD">
      <span class="titleCellFormat">${ _("Number of items")}</span>
    </td>
    <td id="inPlaceNumberItems"></td>
  </tr>

  <tr>
    <td class="titleCellTD">
      <span class="titleCellFormat">${ _("Cache TTL (minutes)")}</span>
    </td>
    <td id="inPlaceCacheTTL"></td>
  </tr>

  <tr>
    <td class="titleCellTD">
      <span class="titleCellFormat">${ _("Observed Events/Categories")}</span>
    </td>
    <td id="categoryEventList"></td>
  </tr>


</table>

<script type="text/javascript">
  $E('inPlaceCacheTTL').set(new InputEditWidget('upcomingEvents.admin.changeCacheTTL', {}, ${ jsonEncode(cacheTTL) }, false, null, null, null).draw());
  $E('inPlaceNumberItems').set(new InputEditWidget('upcomingEvents.admin.changeNumberItems', {}, ${ jsonEncode(numberItems) }, false, null, null, null).draw());

  var categEventSelector = new UpcomingEventFavoritesWidget();
  $E('categoryEventList').set(categEventSelector.draw());

</script>
