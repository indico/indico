<table width="90%%" border="0">
    %(withdrawnNotice)s
    <tr>
        <td>
            <table width="100%%" align="left" border="0" style="border-right:1px solid #777777">
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Contribution ID")%></span></td>
                    <td bgcolor="white">%(id)s</td>
                    <td align="right">
                        <table border="0" cellspacing="1" cellpadding="0">
                            <tr>
                                <td bgcolor="white" align="right" width="10">
                                    <a href="%(contribXML)s" target="_blank"><img src="%(xmlIconURL)s" alt="<%= _("print the current contribution")%>" border="0"> </a>
                                </td>
                                <td bgcolor="white" align="right" width="10">
                                    <a href="%(contribPDF)s" target="_blank"><img src="%(printIconURL)s" alt="<%= _("print the current contribution")%>" border="0"> </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
                    <td bgcolor="white" class="blacktext"><b>%(title)s</b></td>
                    <form action="%(dataModificationURL)s" method="POST">
                    <td rowspan="%(rowspan)s" valign="bottom" align="right" width="1%%">
                        <input type="submit" class="btn" value="<%= _("modify")%>">
                    </td>
                    </form>
                </tr>
                <%
                if self._rh._target.getConference().getAbstractMgr().isActive() and self._rh._target.getConference().hasEnabledSection("cfa") and self._rh._target.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
                %>
                %(additionalFields)s
                <%end%>
                <%
                    else:
                %>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Description")%></span></td>
                    <td bgcolor="white" class="blacktext">
                    %(description)s
                    </td>
                </tr>
                <%end%>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Place")%></span</td>
                    <td bgcolor="white" class="blacktext">%(place)s</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Date/time")%></span</td>
                    <td bgcolor="white" class="blacktext" colspan="2">
		      <% if contrib.isScheduled(): %>
                        <%= self.htmlText(self._contrib.getAdjustedStartDate().strftime("%A %d %B %Y %H:%M")) %>
		      <% end %>
		      <% else: %>
		        <em><%= _("Not scheduled")%></em>
		      <% end %>
		    </td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Duration")%></span</td>
                    <td bgcolor="white" class="blacktext">%(duration)s</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Type")%></span</td>
                    <td bgcolor="white" class="blacktext">%(type)s</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Keywords")%></span</td>
                    <td bgcolor="white" class="blacktext"><pre>%(keywords)s</pre></td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                <% if eventType == "conference":%>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Track")%></span></td>
                    <td bgcolor="white" class="blacktext" colspan="2">
                        <table width="100%%">
                            <tr>
                                <td width="100%%">%(track)s</td>
                                <form action=%(setTrackURL)s method="POST">
                                <td valign="bottom" align="right">
                                    <select name="selTrack">%(selTracks)s</select><input type="submit" class="btn" name="change" value="<%= _("change")%>">
                                </td>
                                </form>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Session")%></span></td>
                    <td bgcolor="white" class="blacktext" colspan="2">
                        <table width="100%%">
                            <tr>
                                <td width="100%%">%(session)s</td>
                                <form action=%(setSessionURL)s method="POST">
                                <td valign="bottom" align="right">
                                    <select name="selSession">%(selSessions)s</select><input type="submit" class="btn" name="change" value="<%= _("change")%>">
                                </td>
                                </form>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Primary authors")%></span</td>
                    <td bgcolor="white" class="blacktext" colspan="2">%(primAuthTable)s</td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Co-authors")%></span</td>
                    <td bgcolor="white" class="blacktext" colspan="2">%(coAuthTable)s</td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                <% end %>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"><% if eventType == "conference":%><%= _("Presenters")%><%end%><%else:%><%= _("Speakers")%><%end%></span</td>
                    <td bgcolor="white" class="blacktext" colspan="2">
                        <table width="100%%">
                            <tr>
                                <td colspan="2" width="100%%">
                                    <form style="padding:0px;margin:0px;" action=%(remSpeakersURL)s method="POST">
                                        %(speakers)s
                                </td>
                                <td valign="bottom" align="right">
                                        <input type="submit" class="btn" name="remove" value="<%= _("remove")%>">
                                    </form>
                                    <% if eventType == "conference":%>
                                    <form style="padding:0px;margin:0px;" action=%(addSpeakersURL)s method="POST">
                                        <table cellspacing="0px" cellpadding="0px" border="0"><tr><td>
                                        <select name="selAuthor">%(authorsForSpeakers)s</select></td>
                                        <td><input type="submit" class="btn" name="add" value="<%= _("add")%>">
                                        </td></tr></table>
                                    </form>
                                    <%end%>
                                    <form style="padding:0px;margin:0px;" action=%(newSpeakerURL)s method="POST">
                                        <input type="submit" class="btn" name="new" value="<%= _("new")%>">
                                    </form>
                                    <form style="padding:0px;margin:0px;" action=%(searchSpeakersURL)s method="POST">
                                        <input type="submit" class="btn" name="search" value="<%= _("search")%>">
                                </td>
                                    </form>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Report numbers")%></span</td>
                    <td bgcolor="white" colspan="2"><i>%(reportNumbersTable)s</i></td>
                </tr>
                <tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                <% if eventType == "conference":%>
				%(abstract)s
                %(withdrawnInfo)s
				<tr>
					<td align="center" colspan="3" style="border-top: 2px solid #777777">
						<table align="center" border="0">
							<tr>
								<% if withdrawDisabled: %>
								<form action=%(withdrawURL)s method="POST">
								<td>
									<%= _("This contribution is withdrawn:")%>
									<input type="submit" class="btn" name ="REACTIVATE" value="reactivate">
								</td>

								<% end %>
								<% if not withdrawDisabled: %>

								<form action=%(withdrawURL)s method="POST">
								<td>
                                    <input type="submit" class="btn" value="<%= _("withdraw")%>">
                                </td>
                           		<% end %>
                            </tr>
                        </table>
                    </td>
                </tr>
                <% end %>

            </table>
        </td>
    </tr>
</table>
