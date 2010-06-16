<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

<table width="100%%" align="center">

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
	  <td width="100%%">&nbsp;<td>
	</tr>
        <%
          if not self._rh._target.getConference().getAbstractMgr().isActive() or not self._rh._target.getConference().hasEnabledSection("cfa") or not self._rh._target.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
        %>
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
	  <td width="100%%">&nbsp;<td>
	</tr>
    <%end%>
	<tr>
	  <td>
            <table align="center" width="90%%">
                <%
                if self._rh._target.getConference().getAbstractMgr().isActive() and self._rh._target.getConference().hasEnabledSection("cfa") and self._rh._target.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
                %>
            %(additionalFields)s
                <%end%>
	    <tr>
	      <td align="right" valign="top" class="displayField"><b><%= _("Id")%>:</b></td>
              <td>%(id)s</td>
            </tr>
	    %(location)s
		    <tr>
		        <td align="right" valign="top" class="displayField"><b><%= _("Starting date")%>:</b></td>
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
		        <td align="right" valign="top" class="displayField"><b><%= _("Duration")%>:</b></td>
			<td width="100%%">%(duration)s</td>
		    </tr>
					%(contribType)s
					%(primaryAuthors)s
					%(coAuthors)s
                    %(speakers)s
                    <% if Contribution.canUserSubmit(self._aw.getUser()) or Contribution.canModify(self._aw): %>
                        <td class="displayField" nowrap="" align="right" valign="top">
                            <b>Material:</b>
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
                    <% if Contribution.getConference() and Contribution.getConference().hasEnabledSection('paperReviewing') and Contribution.getConference().getConfReview().hasReviewing() : %>
                        <% if Contribution.canUserSubmit(self._aw.getUser()): %>
                        <tr>
                            <td align="right" valign="top" class="displayField" style="border-right:5px solid #FFFFFF;" nowrap>
                                <b>Reviewing status:</b>
                            </td>
                            <% if not Contribution.getReviewManager().getLastReview().isAuthorSubmitted(): %>
                                    <td>
                                        <form action="<%=urlHandlers.UHContributionSubmitForRewiewing.getURL(Contribution)%>" method="POST">
                                            <input type="submit" class="btn" value="Mark materials as submitted" >
                                        </form>
                                    </td>
                                </tr>
                                <tr>
                                    <td></td>
                                    <td>
                                        Note: Press this button to submit your materials for reviewing.<br>
                                        By doing this you will lock your materials until they are reviewed.
                                    </td>
                            <% end %>
                            <% else: %>
                                    <td style="border-left:5px solid #FFFFFF;">
                                        <%= "<br>".join(Contribution.getReviewManager().getLastReview().getReviewingStatus(forAuthor = True)) %>
                                    </td>
                                </tr>
                                <% if not Contribution.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted(): %>
                                    <tr><td>&nbsp;</td></tr>
                                    <tr><td>&nbsp;</td></tr>
                                    <tr>
                                        <td colspan="2" align="center">
                                            <form action="<%=urlHandlers.UHContributionRemoveSubmittedMarkForReviewing.getURL(Contribution)%>" method="POST">
                                                <input type="submit" class="btn" value="UNMARK materials as submitted" >
                                            </form>
                                        </td>
                                    <tr>
                                        <td colspan="2" align="center">
                                            <font color="red">
                                                Press this button only if you made some mistake when submitting the materials.<br>
                                                The reviewing team will be notified and the reviewing process will be stopped until you mark the materials as submitted again.
                                            </font>
                                        </td>
                                <% end %>
                            <% end %>
                        </tr>
                        <% end %>
                    <% end %>
                 </table>
                 </td>
              </tr>
              <tr><td>%(reviewingStuffDisplay)s</td></tr>
              <tr><td>&nbsp;</td></tr>
              <tr><td>&nbsp;</td></tr>
              <% if Contribution.getConference() and Contribution.getConference().hasEnabledSection('paperReviewing') and Contribution.getConference().getConfReview().hasReviewing() and len(Contribution.getReviewManager().getVersioning()) > 1: %>
                  <tr>
                      <td align="center" class="displayField" nowrap>
                            <b>Reviewing history</b>
                      </td>
                  </tr>
                  <tr>
                      <td colspan="2">
                           %(reviewingHistoryStuffDisplay)s
                      </td>
                  </tr>
              <% end %>
              </table>
           </td>
        </tr>

        </table>
    </td>
</tr>

</table>
