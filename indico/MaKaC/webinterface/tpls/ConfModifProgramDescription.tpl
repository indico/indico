<div class="groupTitle"><%= _("Program description")%></div>
<table width="100%%" align="left" border="0" >
    <tr>
        <td>
            <form action="%(submitURL)s" method="POST">
                <textarea name="description" rows="10" cols="80" >%(description)s</textarea>
        </td>
    </tr>
    <tr>
        <td>
            <input type="submit" name="Save" value="Save" class="btn"> <input type="submit" name="Cancel" class="btn" value="<%= _("Cancel")%>">
            </form>
        </td>
    </tr>
</table>
