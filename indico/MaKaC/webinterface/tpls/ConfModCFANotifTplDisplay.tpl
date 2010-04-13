<table width="90%%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Name")%></span></td>
        <td bgcolor="white" width="100%%"><b>%(name)s</b></td>
        <td valign="bottom" rowspan="7" bgcolor="white" width="100%%">
            <form action=%(modifDataURL)s method="POST">
                <input type="submit" class="btn" value="<%= _("modify")%>">
            </form>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Description")%></span></td>
        <td bgcolor="white" width="100%%"><b>%(description)s</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("From")%></span></td>
        <td bgcolor="white" width="100%%"><b>%(from)s</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("To addresses")%></span></td>
        <td bgcolor="white" width="100%%"><b>%(toAddrs)s</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Cc addresses")%></span></td>
        <td bgcolor="white" width="100%%"><b>%(CCAddrs)s</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Subject")%></span></td>
        <td bgcolor="white" width="100%%"><b>%(subject)s</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Body")%></span></td>
        <td bgcolor="white" width="100%%"><pre>%(body)s</pre></td>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Conditions")%></span></td>
        <td width="100%%" colspan="2">
            <table width="100%%">
                <tr>
                    <form action=%(remConditionsURL)s method="POST">
                    <td width="100%%">
                            %(conditions)s
                    </td>
                    <td align="right" valign="bottom" nowrap>
						</form>
                        <form action=%(newConditionURL)s method="POST">
                            <select name="condType">%(availableConditions)s</select><input type="submit" class="btn" value="<%= _("create new condition")%>">
                    </td>
					</form>
                </tr>
            </table>
        </td>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>

