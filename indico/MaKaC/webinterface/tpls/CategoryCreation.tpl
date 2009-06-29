
<form action="%(postURL)s" method="POST">
    %(locator)s
    <table class="groupTable">
        <tr>
            <td colspan="2"><div class="groupTitle"><%= _("Creation of a new sub-category")%></div></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Name")%></span></td>
            <td class="blacktext"><input type="text" name="name"></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Description")%></span></td>
            <td class="blacktext">
                <textarea name="description" cols="43" rows="6"></textarea>
            </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Default lectures style")%></span></td>
            <td class="blacktext"><select name="defaultSimpleEventStyle">%(simple_eventStyleOptions)s</select></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Default meetings style")%></span></td>
            <td class="blacktext"><select name="defaultMeetingStyle">%(meetingStyleOptions)s</select></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Default Timezone")%></span></td>
            <td class="blacktext"><select name="defaultTimezone">%(timezoneOptions)s</select></td>
        </tr>
        <tr>
            <td>&nbsp;</td>
            <td>
                <input type="submit" class="btn" name="OK" value="<%= _("ok")%>">
                <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
            </td>
        </tr>
    </table>
</form>
