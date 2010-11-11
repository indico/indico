<% declareTemplate(newTemplateStyle=True) %>
<% from MaKaC.reviewing import ConferencePaperReview %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.utils import formatDateTime %>

<% format = "%a %d %b %Y at %H\x3a%M" %>

<div style="padding-left: 10px; padding-top: 10px; padding-bottom: 10px">
<em><%= _("The reviewing mode chosen for this conference is")%>: <%= ConferenceChoiceStr%></em>
</div>

<% if ConferenceChoice == 2 or ConferenceChoice == 4: %>
<table class="newsDisplayItem" width="90%%" align="center" border="0" style="margin-bottom: 1em">
    <!-- Assign or remove a referee -->
    <tr>
        <td id="assignRefereeHelp" colspan="5" class="groupTitle" style="border: none; padding-bottom:10px;"><%= _("Assign a Referee")%></td>
    </tr>

        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Referee")%>:</span>
            </td>
            <% if not ContributionReviewManager.hasReferee(): %>
            <td width="60%%" class='bottom_line' style="padding-bottom: 10px;">
                <%= _("not assigned yet")%>
            </td>
            <% end %>
            <% else: %>
            <td width="60%%" class='bottom_line'>
                <%= ContributionReviewManager.getReferee().getFullName() %>
            </td>
            <% if CanAssignReferee: %>
            <tr>
            <td>&nbsp;</td>
            <td align="left" style="padding-top: 5px; padding-bottom: 15px;">
                 <form id="removeReferee" action="<%= removeAssignRefereeURL %>" method="post" onsubmit="<%=removeRefereeConfirm%>">
                    <input type="submit" class=btn value="Remove">
                </form>
            </td>
            </tr>
            <% end %>
            <% end %>
        </tr>
        <% if ContributionReviewManager.hasReferee(): %>
            <tr>
	            <td class="dataCaptionTD">
	                <span class="dataCaptionFormat"><%= _("Deadline")%></span>
	            </td>
	            <td class="blacktext">
	                <span id="inPlaceEditRefereeDueDate">
	                    <% date = ContributionReviewManager.getLastReview().getAdjustedRefereeDueDate() %>
	                    <% if date is None: %>
	                        <%= _("Date not set yet.")%>
	                    <% end %>
	                    <% else: %>
	                        <%= formatDateTime(date) %>
	                    <% end %>
	                </span>
	            </td>
	        </tr>
        <% end %>
        <% else: %>
        <tr>
            <td>&nbsp;</td>
            <td  width="60%%" class='bottom_line'>
                <span class="titleCellFormat"><%= _("Choose a referee to assign from the list")%>:</span>
            </td>
         </tr>
         <tr>
            <td>&nbsp;</td>
            <form action="<%=assignRefereeURL%>" method="post">
            <% showAssignButton = False %>
            <td width="80%%" class='bottom_line' style="padding-top: 10px;">
                <% if CanAssignReferee: %>
                    <% if len(ConfReview.getRefereesList()) == 0: %>
                        <%= _("No referees proposed for this conference.")%>
                    <% end %>
                    <% else: %>
                        <% showAssignButton = True %>
                        <table cellspacing="0" cellpadding="5">
                        <% first = True %>
                        <% for r in ConfReview.getRefereesList(): %>
                            <tr>
                                <td>
                                    <input type="radio" name="refereeAssignSelection" value="<%= r.getId() %>"
                                    <% if first: %>
                                        CHECKED
                                        <% first = False %>
                                    <% end %>
                                    >
                                </td>
                                <td align="left">
                                    <%= r.getFullName() %>
                                </td>
                            </tr>
                        <% end %>
                        </table>
                    <% end %>
                <% end %>
                <% else: %>
                    <%= _("You are not allowed to assign referees to this contribution.")%>
                <% end %>
            </td>
            <tr>
            <% if showAssignButton: %>
                <td>&nbsp;</td>
                <td align="left">
                    <input type="submit" class=btn value="Assign">
                </td>
            <% end %>
            </form>
            </tr>
        </tr>
        <% end %>
</table>
<% end %>

<% if ConferenceChoice == 3 or ConferenceChoice == 4: %>
<!-- Assign / remove Editors -->
<table class="newsDisplayItem" width="90%%" align="center" border="0" style="margin-bottom: 1em">
    <tr>
            <td id="assignEditorHelp" colspan="5" class="groupTitle" style="border: none; padding-bottom:10px;"><%= _("Assign a Layout Reviewer")%></td>
    </tr>
    <tr>
	        <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Layout reviewer")%>:</span></td>

	   <% if ContributionReviewManager.hasEditor(): %>
	         <td width="60%%" class='bottom_line'>
	         <%= ContributionReviewManager.getEditor().getFullName() %>
	         </td>
	</tr>
    <tr>
           <td>&nbsp;</td>
           <td align="left" style="padding-top: 5px; padding-bottom: 15px;">
              <form action="<%=removeAssignEditingURL%>" method="post">
                 <input type="submit" class=btn value="Remove">
                </form>
           </td>
      </tr>
      <tr>
           <td class="dataCaptionTD">
	               <span class="dataCaptionFormat"><%= _("Deadline")%></span>
	       </td>
	       <td class="blacktext">
	            <span id="inPlaceEditEditorDueDate">
	            <% date = ContributionReviewManager.getLastReview().getAdjustedEditorDueDate() %>
	            <% if date is None: %>
	                <%= _("Date not set yet.")%>
	            <% end %>
	            <% else: %>
	                 <%= formatDateTime(date) %>
	            <% end %>
	            </span>
	       </td>
      </tr>
      <% end %>
      <% else: %>
	        <td width="60%%" style="padding-bottom: 10px;">
	           <%= _("not assigned yet")%>
	        </td>
    </tr>
    <form action="<%=assignEditingURL%>" method="post">
    <tr>
        <% showAssignButton = False %>
            <% if CanAssignEditorOrReviewers: %>
                <% if not ContributionReviewManager.hasReferee() and not ConferenceChoice == 3: %>
                <td>&nbsp;</td>
                <td>
                    <%= _("Please choose a referee first.")%>
                </td>
                </tr>
                <% end %>
                <% elif len(ConfReview.getEditorsList()) == 0: %>
                <td>&nbsp;</td>
                <td>
                    <%= _("No editors proposed for this conference.")%>
                </td>
                </tr>
                <% end %>
                <% else: %>
                <td>&nbsp;</td>
                <td>
		            <span class="titleCellFormat"><%= _("Choose a layout reviewer to assign from the list")%>:</span>
		        </td>
		        </tr>
		        <tr>
		        <td>&nbsp;</td>
		        <td width="80%%" class='bottom_line'>
                    <% showAssignButton = True %>
                    <table cellspacing="0" cellpadding="5">
                    <% first = True %>
                    <% for e in ConfReview.getEditorsList(): %>
                        <tr>
                            <td>
                                <input type="radio" name="editorAssignSelection" value="<%= e.getId() %>"
                                <% if first: %>
                                    CHECKED
                                    <% first = False %>
                                <% end %>
                                >
                            </td>
                            <td align="left">
                                <%= e.getFullName() %>
                            </td>
                        </tr>
                    <% end %>
                    </table>
                <% end %>
            <% end %>
            <% else: %>
                <%= _("You are not allowed to assign layout reviewers to this contribution.")%>
            <% end %>
        </td>
        <% if showAssignButton: %>
        <\tr>
        <tr>
            <td>&nbsp;</td>
            <td align="left">
                <input type="submit" class=btn value="Assign">
            </td>
        </tr>
        <% end %>
        </form>
        </tr>
    <% end %>
    </tr>
</table>
<% end %>

<% if ConferenceChoice == 2 or ConferenceChoice == 4: %>
<!-- Assign / remove content reviewers -->
<table class="newsDisplayItem" width="90%%" align="center" border="0" style="margin-bottom: 1em">
	    <tr>
	        <td id="assignReviewersHelp" colspan="5" class="groupTitle" style="border: none; padding-bottom:10px;"><%= _("Assign Content Reviewers")%></td>
	    </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Content reviewers")%>:</span></td>
            <% if ContributionReviewManager.hasReviewers(): %>
                <form action="<%=removeAssignReviewingURL%>" method="post">
                <td width="60%%"  class='bottom_line'>
                    <table cellspacing="0" cellpadding="5">
                        <% first = True %>
                        <% for r in ContributionReviewManager.getReviewersList(): %>
                            <tr>
                                <td>
                                    <input type="radio" name="reviewerRemoveAssignSelection" value="<%= r.getId() %>"
                                    <% if first: %>
                                        CHECKED
                                        <% first = False %>
                                    <% end %>
                                    >
                                </td>
                                <td align="left">
                                    <%= r.getFullName() %>
                                </td>
                            </tr>
                        <% end %>
                    </table>
                </td>
                <tr>
                <td>&nbsp;</td>
                <td align="left" style="padding-top: 5px; padding-bottom: 15px;">
                    <input type="submit" class=btn value="Remove">
                </td>
                </tr>
                </form>
                <tr>
                <td class="dataCaptionTD" style="padding-top: 5px; padding-bottom: 15px;">
                    <span class="dataCaptionFormat"><%= _("Deadline")%></span>
                </td>
                <td class="blacktext" style="padding-top: 5px; padding-bottom: 15px;">
                    <span id="inPlaceEditReviewerDueDate">
                    <% date = ContributionReviewManager.getLastReview().getAdjustedReviewerDueDate() %>
                    <% if date is None: %>
                        <%= _("Date not set yet.")%>
                    <% end %>
                    <% else: %>
                        <%= formatDateTime(date) %>
                    <% end %>
                    </span>
                </td>
            </tr>
            <% end %>
            <% else: %>
                <td width="60%%" class='bottom_line' style="padding-bottom: 10px;">
                    <%= _("not assigned yet")%>
                </td>
            <% end %>
            </td>
            </tr>
    <form action="<%=assignReviewingURL%>" method="post">
    <tr>
        <% showAssignButton = False %>
            <% if CanAssignEditorOrReviewers: %>
                <% if not ContributionReviewManager.hasReferee(): %>
                <td>&nbsp;</td>
                <td>
                    <%= _("Please choose a referee first.")%>
                </td>
                </tr>
                <% end %>
                <% elif len(ConfReview.getReviewersList()) == 0: %>
                <td>&nbsp;</td>
                <td>
                    <%= _("No editors proposed for this conference.")%>
                </td>
                </tr>
                <% end %>
                <% elif len(AvailableReviewers) == 0: %>
                <td>&nbsp;</td>
                <td>
                        <%= _("No more content reviewers available to assign in this conference.")%>
                </td>
                </tr>
                <% end %>
                <% else: %>
                <td>&nbsp;</td>
                <td>
                    <span class="titleCellFormat"><%= _("Choose a content reviewer to assign from the list")%>:</span>
                </td>
                </tr>
                <tr>
                <td>&nbsp;</td>
                <td width="80%%" class='bottom_line'>
                    <% showAssignButton = True %>
                    <table cellspacing="0" cellpadding="5">
                    <% first = True %>
                        <% for r in AvailableReviewers: %>
                            <tr>
                                <td>
                                    <input type="radio" name="reviewerAssignSelection" value="<%= r.getId() %>"
                                    <% if first: %>
                                        CHECKED
                                        <% first = False %>
                                    <% end %>
                                    >
                                </td>
                                <td align="left">
                                    <%= r.getFullName() %>
                                </td>
                            </tr>
                        <% end %>
                        </table>
                    <% end %>
                <% end %>
                <% else: %>
                    <%= _("You are not allowed to assign content reviewers to this contribution.")%>
                <% end %>
            </td>
            <% if showAssignButton: %>
            </tr>
            <tr>
                <td>&nbsp;</td>
                <td align="left">
                    <input type="submit" class=btn value="Assign">
                </td>
            <% end %>
            </form>
        </tr>
</table>
<% end %>





<script type="text/javascript">

<% if CanEditDueDates: %>
    <% if ContributionReviewManager.hasReferee(): %>
        new IndicoUI.Widgets.Generic.dateEditor($E('inPlaceEditRefereeDueDate'),
                           'reviewing.contribution.changeDueDate',
                           {conference: '<%= Conference.getId() %>',
                            contribution: '<%= ContributionReviewManager.getContribution().getId() %>',
                            dueDateToChange: 'Referee'},
                           null, true);
    <% end %>

    <% if ContributionReviewManager.hasEditor(): %>
        new IndicoUI.Widgets.Generic.dateEditor($E('inPlaceEditEditorDueDate'),
                           'reviewing.contribution.changeDueDate',
                           {conference: '<%= Conference.getId() %>',
                            contribution: '<%= ContributionReviewManager.getContribution().getId() %>',
                            dueDateToChange: 'Editor'},
                           null, true);
    <% end %>

    <% if ContributionReviewManager.hasReviewers(): %>
        new IndicoUI.Widgets.Generic.dateEditor($E('inPlaceEditReviewerDueDate'),
                           'reviewing.contribution.changeDueDate',
                           {conference: '<%= Conference.getId() %>',
                            contribution: '<%= ContributionReviewManager.getContribution().getId() %>',
                            dueDateToChange: 'Reviewer'},
                           null, true);
    <% end %>

<% end %>


</script>