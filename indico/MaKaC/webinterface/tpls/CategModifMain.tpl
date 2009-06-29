
<div class="groupTitle"><%= _("General Settings")%></div>

<table width="100%%">
<tr>
  <td>
    <table width="90%%" align="left" border="0">
    <tr>
      <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Name")%></span></td>
      <td bgcolor="white" width="100%%" class="blacktext">%(name)s</td>
      <td rowspan="2" valign="bottom" align="right">
	<form action="%(dataModificationURL)s" method="POST">
	%(dataModifButton)s
	</form>
      </td>
    </tr>
    <tr>
      <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Description")%></span></td>
      <td bgcolor="white" width="100%%" class="blacktext">%(description)s</td>
    </tr>
    <tr>
      <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Default&nbsp;Timezone")%></span></td>
      <td bgcolor="white" width="100%%" class="blacktext">%(defaultTimezone)s</td>
    </tr>
    <tr>
      <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Icon")%></span></td>
      <td bgcolor="white" width="100%%" class="blacktext">%(icon)s</td>
    </tr>
    <tr>
      <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Default&nbsp;lectures style")%></span></td>
      <td bgcolor="white" width="100%%" class="blacktext">%(defaultLectureStyle)s</td>
    </tr>
    <tr>
      <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Default&nbsp;meetings style")%></span></td>
      <td bgcolor="white" width="100%%" class="blacktext">%(defaultMeetingStyle)s</td>
    </tr>
    <tr>
      <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Default&nbsp;events visibility")%></span></td>
      <td bgcolor="white" width="100%%" class="blacktext">%(defaultVisibility)s</td>
    </tr>
    <tr>
      <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr><td></td></tr>
    <!-- <tr>
        <td class="dataCaptionTD">
          <a name="sections"></a>
          <span class="dataCaptionFormat"> <%= _("Management features")%></span>
          <br>
          <br>
          <img src=%(enablePic)s alt="Click to disable"> <small> <%= _("Enabled feature")%></small>
          <br>
          <img src=%(disablePic)s alt="Click to enable"> <small> <%= _("Disabled feature")%></small>
        </td>
        <td bgcolor="white" width="100%%" class="blacktext" style="padding-left:20px">
            <table align="left">
            <tr>
              <td>
				%(tasksManagement)s
              </td>
            </tr>
            </table>
        </td>
    </tr>
    <tr><td></td></tr>
    <tr>
      <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>-->    
    </table>
  </td>
</tr>
<tr>
  <td>
    <table width="90%%" align="left" border="0">
    <tr>
      <td class="dataCaptionTD">
	<span class="dataCaptionFormat"> <%= _("Contents")%></span>
      </td>
      <td>
	<form action="%(removeItemsURL)s" name="contentForm" method="POST">
	%(locator)s
	<table width="100%%">
	<tr>
	  <td bgcolor="white" width="100%%">
	    %(items)s
	  </td>
	  <td align="center">
	    <table cellspacing="0" cellpadding="0" align="right">
	    <tr>
	      <td align="right" valign="bottom">
		<input type="submit" class="btn" name="sort" value="<%= _("sort alphabetically")%>">
	      </td>
	    </tr>
	    <tr>
	      <td align="right" valign="bottom">
		<input type="submit" class="btn" name="remove" value="<%= _("remove")%>">
	      </td>
	    </tr>
	    <tr>
	      <td align="right" valign="bottom">
		<input type="submit" class="btn" name="reallocate" value="<%= _("re-allocate")%>">
	      </td>
	    </tr>
	    <tr>
	      <td align="right" valign="bottom">
		<input type="submit" class="btn" value="<%= _("add subcateg")%>" onClick="this.form.action='%(addSubCategoryURL)s';">
	      </td>
	    </tr>
	    </table>
	  </td>
	</tr>
	</table>
	</form>
      </td>
    </tr>
    <tr>
      <td colspan="2" class="horizontalLine">&nbsp;</td>
    </tr>
    </table>
  </td>
</tr>
</table>

<script type="text/javascript">

function selectAll()
{
	if (!document.contentForm.selectedConf.length){
		document.contentForm.selectedConf.checked=true
    } else {
		for (i = 0; i < document.contentForm.selectedConf.length; i++) {
		    document.contentForm.selectedConf[i].checked=true
    	}
	}
}

function deselectAll()
{
	if (!document.contentForm.selectedConf.length)	{
	    document.contentForm.selectedConf.checked=false
    } else {
	   for (i = 0; i < document.contentForm.selectedConf.length; i++) {
	       document.contentForm.selectedConf[i].checked=false
       }
	}
}

</script>
