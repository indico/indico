<!-- CONTEXT HELP DIVS -->
<div id="tooltipPool" style="display: none">
    <!-- Where is key? -->
    <div id="defaultLocationCH" class="tip">
        ${ _("First location/location by default offered to users")}
    </div>
    <%include file="CHBookingRepeatition.tpl"/>
</div>
<!-- END OF CONTEXT HELP DIVS -->


<table align="center" width="95%">

<tr>
  <td class="formTitle">${ _("Room Booking Administration")}</td>
</tr>

<!-- ==================== Manage Locations  ==================== -->
<!-- =========================================================== -->
<tr>
  <td>
    <br />
    <table>
    <tr>
      <td colspan="2" class="groupTitle">${ _("Manage Locations")}</td>
    </tr>
    <tr>
      <td class="titleUpCellTD" style="width: 160px;"><span class="titleCellFormat">${ _("Available locations")}</span></td>
      <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
        % if len(Location.allLocations) > 0:
        <form action="${urlHandlers.UHRoomBookingDeleteLocation.getURL() }" method="POST">
          <p>
                % for loc in Location.allLocations:
                    <input type="radio" name="removeLocationName" id="removeLocationName" value="${ loc.friendlyName }"><a href="${ urlHandlers.UHRoomBookingAdminLocation.getURL(loc) }">${ loc.friendlyName }</a><br>
                % endfor
            <input type="submit" class="btn" value="${ _("Remove")}" />
          </p>
        </form>
        % endif
        <form action="${urlHandlers.UHRoomBookingSaveLocation.getURL() }" method="POST">
          <p>
            <input type="text" id="newLocationName" name="newLocationName" value="" size="28" />
            <select name="pluginName">
            % for plugin in Location.getAvailablePlugins():
              <option value="${plugin.__plugin_id__}">${plugin.__metadata__['name']}</option>
            % endfor
            </select>
            <input type="submit" class="btn" value="${ _("Add")}" />
          </p>
        </form>
      </td>
    </tr>
    % if len(Location.allLocations) > 0:
    <tr>
      <td class="titleUpCellTD" style="width: 160px;"><span class="titleCellFormat">${ _("Default location")}</span></td>
      <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
        <form action="${urlHandlers.UHRoomBookingSetDefaultLocation.getURL() }" method="POST">
            <select name="defaultLocation" id="defaultLocation">
                <% defaultLoc = Location.getDefaultLocation().friendlyName %>
                % for loc in Location.allLocations:
                    <option value="${loc.friendlyName}" ${' selected="selected" ' if loc.friendlyName == defaultLoc else ""} >${ loc.friendlyName }</option>
                % endfor
            </select>
            <input type="submit" class="btn" value="${ _("Change")}">
            ${contextHelp('defaultLocationCH' )}
        </form>
      </td>
    </tr>
    % endif
    </table>
    <br />
  </td>
</tr>
</table>
