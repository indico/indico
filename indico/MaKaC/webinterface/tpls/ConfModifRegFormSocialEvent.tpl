<table width="90%%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">%(title)s</td>
		<form action=%(dataModificationURL)s method="POST">
        <td rowspan="3" valign="bottom" align="right">
			<input type="submit" class="btn" value="<%= _("modify")%>">
        </td>
		</form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Description")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext"><pre>%(description)s</pre></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Introduction sentence")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">%(intro)s</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Selection type")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">%(selectionType)s</td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Social event entries")%></span></td>
        <td bgcolor="white" class="blacktext" colspan="2" width="100%%">
            <table width="100%%">
                <tr>
                    <form action=%(postURL)s method="POST">
                    <td width="100%%">
                        %(socialEvents)s
                    </td>
                    <td valign="bottom" align="right">
                        <input type="submit" class="btn" name="remove" value="<%= _("remove")%>" style="width:80px">
                        </form>
                        <form action=%(postNewURL)s method="POST">
                            <input type="submit" class="btn" name="add" value="<%= _("add")%>" style="width:80px">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>
