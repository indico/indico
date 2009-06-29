<form action=%(postURL)s method="POST">    

    <table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td colspan="2" class="groupTitle"><%= _("Send Email")%></font></b></td>
        </tr>
        <tr>
            <td>To: </td>
	  		<td>%(toField)s</td>
		</tr>
       	<tr>
            <td>Cc: </td>
  	    	<td><input type="text" name="cc" size="50" value="%(cc)s"></text></td>
        </tr>
        <tr>
            <td>From: </td>
  	    <td>%(fromField)s</td>
        </tr>
       	<tr>
            <td>Subject:</td>
	    	<td><input type="text" name="subject" size="50" value="%(subject)s"></text></td>
        </tr>
       	<tr>
            <td valign="top">Body:</td>
	    	<td><textarea name="body" rows="15" cols="85">%(body)s</textarea></td>
        </tr>
        <tr>
            <td colspan="2" align="center">
                <input type="submit" class="btn" name="OK" value="<%= _("send")%>">
                <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
            </td>
        </tr>
    </table>
</form>
