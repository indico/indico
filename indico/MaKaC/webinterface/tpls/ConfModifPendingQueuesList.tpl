<% declareTemplate(newTemplateStyle=True) %>

<form action="<%= postURL %>" method="post">
    <table width="90%" align="center" border="0">
        <tr>
            <td align="center" colspan="3">
                <em><%= title %></em>
            </td>
        </tr>
        <tr>
            <td bgcolor="white">
                <table width="100%" cellspacing="0" align="center" border="0">
                    <tr>
                        <td>
                        </td>
                        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF; \
                                                    border-bottom: 1px solid #5294CC;">
						<%= _("Name/email")%>
                        </td>
                        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px \
                                                    solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                            <%= target %>
                        </td>
                    </tr>

		    <% if len(list) == 0: %>
		     <tr><td colspan=\"11\"><br><center><%= _("No pending requests")%></center></td></tr>
		    <% end %>

		    <% for (key, pList) in list: %>
                    <tr>
                      <td valign="top"><input type="checkbox" name="pendingSubmitters" value="<%= str(key) %>"></td>
                      <td valign="top" nowrap class="abstractLeftDataCell"><%= self.htmlText("%s <%s>"%(pList[0].getAbrName() or "&nbsp;", pList[0].getEmail() or "&nbsp;")) %></td>
                      <td width="100%%" valign="top" align="left" class="abstractDataCell" style="padding-left:20px">
			<% pList.sort(self._cmpByContribName) %>
			<% for cp in pList: %>
                        <% contrib=cp.getContribution() %>
			<a href="<%= str(urlHandlers.UHContributionModification.getURL(contrib)) %>"><%= self.htmlText(contrib.getTitle()) %></a> 
			 <% if pType == _("Submitters"): %>
			  <small>
			   <% if contrib.isPrimaryAuthor(cp): %>
			    <%= _("Primary Author")%>
			   <% end %>
			   <% elif contrib.isCoAuthor(cp): %>
			    <%= _("Co-Author")%>
			   <% end %>
			   <% elif contrib.isSpeaker(cp): %>
			    <%= _("Speaker")%>
			   <% end %>
			   <% else: %>
			    unkwon
			   <% end %>
			  </small>			
			 <% end %>
			<% end %>
		      </td>
                    </tr>
		    <% end %>

                </table>
            </td>
        </tr>
        <tr>
            <td>
                &nbsp;
            </td>
        </tr>
        <tr>
            <td colspan="11" style="border-top:2px solid #777777;padding-top:5px" valign="bottom" align="left">
                &nbsp;
            </td>
        </tr>
        <tr>
            <td colspan="10" valign="bottom" align="left">
                <input type="submit" class="btn" name="remove" value="<%= _("remove selected")%>">
            </td>
        </tr>
        <tr>
            <td colspan="10" valign="bottom" align="left">
                <input type="submit" class="btn" name="reminder" value="<%= _("send reminder")%>">
            </td>
        </tr>
    </table>
</form>
