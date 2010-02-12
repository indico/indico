<br/>
<table>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Current status")%></span></td>
    <td class="blacktext" colspan="2">
      <form action="%(setStatusURL)s" method="POST">
	<div>
	  <input name="changeTo" type="hidden" value="%(changeTo)s" />
	  <b>%(status)s</b>
	  <small><input type="submit" class="btn" value="%(changeStatus)s" /></small>
	</div>
      </form>
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Registration start date")%></span></td>
    <td class="blacktext">
      %(startDate)s
    </td>
    <td rowspan="8" style="align: right; vertical-align: bottom;">
      <form action="%(dataModificationURL)s" method="POST">
	<div>
	  <input type="submit" class="btn" value="<%= _("modify")%>" %(disabled)s />
	</div>
      </form>
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Registration end date")%></span></td>
    <td class="blacktext">
      %(endDate)s
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Modification end date")%></span></td>
    <td class="blacktext">
      %(modificationEndDate)s
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
    <td class="blacktext">
      %(title)s
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Contact info")%></span></td>
    <td class="blacktext">
      %(contactInfo)s
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Announcement")%></span></td>
    <td class="blacktext">
      <pre>%(announcement)s</pre>
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Max No. of registrants")%></span></td>
    <td class="blacktext">
      %(usersLimit)s
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Email notification (on new registrations)")%></span></td>
    <td class="blacktext">
      %(notification)s
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Must have account")%></span></td>
    <td class="blacktext">
      %(mandatoryAccount)s
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Currency")%></span></td>
    <td class="blacktext">
      %(Currency)s
    </td>
  </tr>
  <tr>
    <td colspan="3" class="horizontalLine">&nbsp;</td>
  </tr>
  <tr>
    <td class="dataCaptionTD">
      <a name="personalfields"></a>
      <span class="dataCaptionFormat"><%= _("Personal Data")%></span>
      <br/>
      <br/>
      <img src=%(enablePic)s alt="<%= _("Click to disable")%>"> <small><%= _("Enabled field") %></small>
      <br/>
      <img src=%(disablePic)s alt="<%= _("Click to enable")%>"> <small><%= _("Disabled field") %></small>
    </td>
    <td class="blacktext" style="padding-left:20px">
      %(personalfields)s
    </td>
    <td>
    </td>
  </tr>
  <tr>
    <td colspan="3" class="horizontalLine">&nbsp;</td>
  </tr>
  <tr>
    <td class="dataCaptionTD">
      <a name="sections"></a>
      <span class="dataCaptionFormat"><%= _("Sections of the form")%></span>
      <br/>
      <br/>
      <img src=%(enablePic)s alt="<%= _("Click to disable")%>"> <small> <%= _("Enabled section")%></small>
      <br/>
      <img src=%(disablePic)s alt="<%= _("Click to enable")%>"> <small> <%= _("Disabled section")%></small>
    </td>
    <form action=%(actionSectionURL)s method="POST">
      <td class="blacktext" style="padding-left:20px">
	%(sections)s
      </td>
      <td>
	<input type="submit" class="btn" name="removeSection" value="<%= _("remove sect.")%>" />
	<input type="submit" class="btn" name="newSection" value="<%= _("new sect.")%>" />
      </td>
    </form>
  </tr>
  <tr>
    <td colspan="3" class="horizontalLine">&nbsp;</td>
  </tr>
  <tr>
    <td class="dataCaptionTD">
      <span class="dataCaptionFormat"> <%= _("Statuses definition")%></span>
    </td>
    <td colspan="2">
      <form action=%(actionStatusesURL)s method="POST">
	<table>
	  <tr>
	    <td colspan="2">
	      <input type="text" name="caption" value="" size="50" />
	      <input type="submit" class="btn" name="addStatus" value="<%= _("add status")%>" />
	    </td>
	  </tr>
	  <tr>
	    <td>%(statuses)s</td>
	    <td>
	      <input type="submit" class="btn" name="removeStatuses" value="<%= _("remove status")%>" />
	    </td>
	  </tr>
	</table>
      </form>
    </td>
  </tr>
  <tr>
    <td colspan="3" class="horizontalLine">&nbsp;</td>
  </tr>
</table>
<br/>

