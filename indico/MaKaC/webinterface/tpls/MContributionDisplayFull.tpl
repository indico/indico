<br><table width="100%%" align="center">
    <tr>
        <td align="center">
            <form action=%(submitURL)s method="POST">
            %(submitBtn)s
            </form>
        </td>
    </tr>
    <tr>
        <td>
	    <table align="center" width="95%%" border="0" style="border: 1px solid #777777;">
            <tr>
                <td>&nbsp;</td>
            </tr>
            <tr>
                <td>
		            <table align="center" width="95%%" border="0">
                        %(withdrawnNotice)s
		            <tr>
                        <td align="center">%(modifIcon)s%(submitIcon)s<font size="+1" color="black"><b>%(title)s</b></font></td>
		            </tr>

		            <tr>
		                <td>
                            <table align="center">
                                <tr>
                                    <td>%(description)s</td>
                                </tr>
                            </table>
                        </td>
		            </tr>

		            <tr>
		                <td>
		                    <table align="center" width="90%%">
		                        <tr>
		                            <td align="right" valign="top" class="displayField"><b> <%= _("Id")%>:</b></td>
                                    <td>%(id)s</td>
            </tr>
		    %(location)s
		    <tr>
		        <td align="right" valign="top" class="displayField"><b> <%= _("Starting date")%>:</b></td>
			<td width="100%%">
			    <table cellspacing="0" cellpadding="0" align="left">
			    <tr>
			        <td align="right">%(startDate)s</td>
				<td>&nbsp;&nbsp;%(startTime)s</td>
			    </tr>
			    </table>
			</td>
		    </tr>
		    <tr>
		        <td align="right" valign="top" class="displayField"><b> <%= _("Duration")%>:</b></td>
			<td width="100%%">%(duration)s</td>
		    </tr>
					%(contribType)s
					%(primaryAuthors)s
					%(coAuthors)s
                    %(speakers)s
                    <% if Contribution.canUserSubmit(self._aw.getUser()) or Contribution.canModify(self._aw): %>
                    <td class="displayField" nowrap="" align="right" valign="top">
                        <b><%= _("Material:")%></b>
                    </td>
                    <td width="100%%" valign="top">
                        <%=MaterialList%>
                    </td>
                    <% end %>
                    <% else: %>
                        %(material)s
                    <% end %>
					<tr><td>&nbsp;</td></tr>
                    %(inSession)s
                    %(inTrack)s
					<tr><td>&nbsp;</td></tr>
                    %(subConts)s
                 </table>
                 </td>
              </tr>
              </table>
           </td>
        </tr>
        </table>
    </td>
</tr>
<tr>
    <td align="center">
        <form action=%(submitURL)s method="POST">
        %(submitBtn)s
        </form>
    </td>
</tr>
</table>
