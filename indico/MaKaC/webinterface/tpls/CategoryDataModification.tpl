
<form action="%(postURL)s" method="POST" ENCTYPE="multipart/form-data">
    %(locator)s
    <table class="groupTable">
        <tr>
            <td colspan="2"><div class="groupTitle">
                     <%= _("Modification of category basic data")%>
            </div>
            </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Name")%></span></td>
            <td class="blacktext"><input type="text" name="name" size="50" value="%(name)s"></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Description")%></span></td>
            <td class="blacktext">
                <textarea name="description" cols="43" rows="6">%(description)s</textarea>
            </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Icon")%></span></td>
            <td class="blacktext">
                %(icon)s
		<input type="submit" class="btn" name="delete" value="<%= _("delete")%>">
                <br><input type="file" name="icon">
            </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Default lectures style")%></span></td>
            <td class="blacktext"><select name="defaultSimpleEventStyle">%(simple_eventStyleOptions)s</select></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Default meetings style")%></span></td>
            <td class="blacktext"><select name="defaultMeetingStyle">%(meetingStyleOptions)s</select>
            <input type=checkbox name="subcats" value=True> <%= _("Same style in all subcategories")%></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Default Visibility")%></span></td>
            <td class="blacktext">
              <select name="visibility">
              %(visibility)s
              </select>
              </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Default Timezone")%></span></td>
            <td class="blacktext"><select name="defaultTimezone">%(timezoneOptions)s</select>
            <% if not rh._target.getSubCategoryList(): %>
            <input type=checkbox name="modifyConfTZ" value=False><%= _("Modify timezone for all conferences")%></td>
            <%end%>
        </tr>
	<tr>
            <td>&nbsp;</td>
            <td class="blacktext">
                <input type="submit" class="btn" name="OK" value="<%= _("ok")%>">
                <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
            </td>
        </tr>
    </table>
</form>
