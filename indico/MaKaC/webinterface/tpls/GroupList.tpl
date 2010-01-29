<table class="groupTable">
<form action="%(createGroupURL)s" method="POST">

<tr>
  <td colspan="2"><div class="groupTitle"><%= _("Group tools") %></div></td>
</tr>
<tr>
  <td></td>
  <td class="blacktext"><em><%= _("The database currently hosts %(nbGroups)s groups.")%></em></td>
</tr>
<tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Tools")%></span></td>
    <td class="blacktext">
        <input type="submit" value="<%= _("New Group")%>" class="btn" />
    </td>
</tr>  
</form>
<form action="%(browseGroupsURL)s" method="POST" name="browseForm">
<input type="hidden" value="" name="letter">
<tr>
  <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Browse Groups")%></span></td>
  <td>%(browseGroups)s</td>
</tr>
</form>


<form action="%(searchGroupsURL)s" method="POST">

<tr>
    <td colspan="2"><div class="groupTitle"><%= _("Search groups")%></div></td>
</tr>
<tr>
    <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Group name")%></span></td>
    <td><input type="text" name="sName"></td>
</tr>
<tr>
    <td>&nbsp;</td>
    <td><input type="submit" class="btn" value="<%= _("apply")%>" /></td>
</tr>
<tr>
    <td>&nbsp;</td>
    <td>
        <table width="100%%"><tbody>
            %(groups)s
        </tbody></table>
        <br /><br />
    </td>
</tr>

</form>
</table>