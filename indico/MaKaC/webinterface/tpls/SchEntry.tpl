<tr bgcolor="white">
    <td>%(nr)s<td>
    <td align="center">%(moveUpButton)s%(moveDownButton)s</td>
    <td><b><font size="+2">%(description)s</font></b></td>
    <td><form action="%(moveItemURL)s" method="POST">
            %(entryLocator)s
            move <select name="after">
                    <option value="1" selected> <%= _("after")%></option>
                    <option value="0"> <%= _("before")%></option>
                 </select> 
                 <select name="refEntry">%(refEntriesItems)s</select>
                 <input type="submit" class="btn" value="<%= _("do it")%>">
        </form>
    </td>
</tr>
