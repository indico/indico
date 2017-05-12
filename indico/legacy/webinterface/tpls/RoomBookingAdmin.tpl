<!-- CONTEXT HELP DIVS -->
<div id="tooltipPool" style="display: none">
  <!-- Where is key? -->
  <div id="defaultLocationCH" class="tip">
    ${ _("First location/location by default offered to users")}
  </div>
  <%include file="CHBookingRepetition.tpl"/>
</div>
<!-- END OF CONTEXT HELP DIVS -->


<table align="center" width="95%">

<!-- ==================== Manage Locations  ==================== -->
<!-- =========================================================== -->
<tr>
  <td>
    <table>
    <tr>
      <td class="titleUpCellTD" style="width: 160px;">
        <span class="titleCellFormat">${ _('Available locations')}</span>
      </td>
      <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
        % if locations:
        <form action="${ url_for('rooms_admin.roomBooking-deleteLocation') }" method="POST">
          <input type="hidden" name="csrf_token" value="${ _session.csrf_token }">
          <p>
            % for loc in locations:
              <input type="radio" name="location_id" value="${ loc.id }">
              <a href="${ url_for('rooms_admin.roomBooking-adminLocation', loc) }">
                ${ loc.name }
              </a><br>
            % endfor
            <input type="submit" class="i-button" value="${ _('Remove') }" />
          </p>
        </form>
        % endif
        <form action="${ url_for('rooms_admin.roomBooking-saveLocation') }" method="POST">
          <input type="hidden" name="csrf_token" value="${ _session.csrf_token }">
          <p>
            <input type="text" id="newLocationName" name="newLocationName" value="" size="28" />
            <input type="submit" class="i-button" value="${ _('Add') }" />
          </p>
        </form>
      </td>
    </tr>
    % if locations:
    <tr>
      <td class="titleUpCellTD" style="width: 160px;">
        <span class="titleCellFormat">${ _("Default location") }</span>
      </td>
      <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
        <form action="${ url_for('rooms_admin.roomBooking-setDefaultLocation') }" method="POST">
          <input type="hidden" name="csrf_token" value="${ _session.csrf_token }">
          <select name="location_id" id="defaultLocation">
            % for loc in locations:
              <option value="${ loc.id }" ${' selected' if loc.is_default else ''} >${ loc.name }</option>
            % endfor
          </select>
          <input type="submit" class="i-button" value="${ _('Change') }">
          ${ contextHelp('defaultLocationCH') }
        </form>
      </td>
    </tr>
    % endif
    </table>
    <br />
  </td>
</tr>
</table>
