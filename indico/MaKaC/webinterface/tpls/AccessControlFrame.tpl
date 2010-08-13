<%!
#Special case for categories
if isFullyPublic == None :
    isFullyPublic = True

%>

<table class="groupTable">
<tr>
  <td colspan="5"><div class="groupTitle"><%= _("Access control")%></div></td>
</tr>
<% if type == 'Home' : %>
<% includeTpl('HomeAccessControlStatusFrame', setPrivacyURL=setPrivacyURL, privacy=privacy, locator = locator) %>
<% end %>
<% else : %>
<% includeTpl('AccessControlStatusFrame', parentName=parentName, privacy=privacy, \
    parentPrivacy=parentPrivacy, statusColor = statusColor, parentStatusColor=parentStatusColor,
    locator=locator, isFullyPublic=isFullyPublic) %>
<% end %>
</table>

