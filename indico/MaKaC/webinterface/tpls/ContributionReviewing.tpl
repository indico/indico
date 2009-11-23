<% declareTemplate(newTemplateStyle=True) %>
<% from MaKaC.reviewing import ConferenceReview %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.utils import formatDateTime %>

<% format = "%a %d %b %Y at %H\x3a%M" %>


<% if not Review.isAuthorSubmitted(): %>
<table width="90%%" align="center" border="0" style="margin-bottom: 1em">
    <% if len(Review.getReviewManager().getVersioning()) == 1: %>
    <tr>
        <td>
            <span style="color:red;">
            <%= _("Warning: the author(s) of this contribution have still not marked their initial materials as submitted.")%><br>
            <%= _("You must wait until then to start the reviewing process.")%>
            </span>
        </td>
    </tr>
    <% end %>
    <% else: %>
    <tr>
        <td>
            <span style="color:red;">
            <%= _("Warning: since this contribution was marked 'To be corrected', the author(s) has not submitted new materials.")%><br>
            <%= _("You must wait until then to restart the reviewing process.")%><br>
            </span>
        </td>
    </tr>
    <% end %>
</table>
<% end %>

<table width="90%%" align="center" border="0" style="margin-bottom: 1em">
    <!-- Assign or remove a referee -->
    <tr>
        <td id="assignRefereeHelp" colspan="5" class="groupTitle" style="border: none; padding-bottom:10px;"><%= _("Assign a Referee")%></td>
    </tr>
    <% if ConferenceChoice == 2 or ConferenceChoice == 4: %>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Assigned referee")%></span>
            </td>
            <% if not ContributionReviewManager.hasReferee(): %>
            <td width="60%%" class='bottom_line'>
                <%= _("No referee assigned to this contribution.")%>
            </td>
            <% end %>
            <% else: %>
            <td width="60%%" class='bottom_line'>
                <%= ContributionReviewManager.getReferee().getFullName() %>
            </td>
            <td align="right">
                <form action="<%=removeAssignRefereeURL %>" method="post">
                    <input type="submit" class=btn value="remove">
                </form>
            </td>
            <% end %>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Assign a referee to this contribution")%></span>
            </td>
            <form action="<%=assignRefereeURL%>" method="post">
            <% showAssignButton = False %>
            <td width="80%%" class='bottom_line'>
                <% if CanAssignReferee: %>
                    <% if len(ConfReview.getRefereesList()) == 0: %>
                        <%= _("No referees proposed for this conference.")%>
                    <% end %>
                    <% elif ContributionReviewManager.hasReferee(): %>
                        <%= _("You can only add one referee for a given contribution.")%>
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
            <% if showAssignButton: %>
                <td align="right">
                    <input type="submit" class=btn value="assign">
                </td>
            <% end %>
            </form>
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
    <% end %>
    <% else: %>
    <tr>
        <td colspan="5">
            <%= _("This conference does not enable content reviewing. The editor's judgement is the only judgement.")%>
        </td>
    </tr>
    <% end %>
</table>

<!-- Assign / remove Editors -->
<table width="90%%" align="center" border="0" style="margin-bottom: 1em">
    <tr>
        <td id="assignEditorHelp" colspan="5" class="groupTitle" style="border: none; padding-bottom:10px;"><%= _("Assign a Layout Reviewer")%></td>
    </tr>
    <% if ConferenceChoice == 3 or ConferenceChoice == 4: %>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Assigned layout reviewer")%></span></td>
        
        <% if not ContributionReviewManager.hasEditor(): %>
            <td width="60%%" class='bottom_line'>
                <%= _("No layout reviewer assigned to this contribution.")%>
            </td>
            <% end %>
            <% else: %>
            <td width="60%%" class='bottom_line'>
                <%= ContributionReviewManager.getEditor().getFullName() %>
            </td>
            <td align="right">
                <form action="<%=removeAssignEditingURL%>" method="post">
                    <input type="submit" class=btn value="remove">
                </form>
            </td>
            <% end %>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat"><%= _("Assign a layout reviewer to this contribution")%></span>
        </td>
        <form action="<%=assignEditingURL%>" method="post">
        <% showAssignButton = False %>
        <td width="80%%" class='bottom_line'>
            <% if CanAssignEditorOrReviewers: %>
                <% if len(ConfReview.getEditorsList()) == 0: %>
                    <%= _("No editors proposed for this conference.")%>
                <% end %>
                <% elif ContributionReviewManager.hasEditor(): %>
                    <%= _("You can only add one layout reviewer for a given contribution.")%>
                <% end %>
                <% elif not ContributionReviewManager.hasReferee() and not ConferenceChoice == 3: %>
                    <%= _("Please choose a referee first.")%>
                <% end %>
                <% else: %>
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
            <td align="right">
                <input type="submit" class=btn value="assign">
            </td>
        <% end %>
        </form>
    </tr>
    <% if ContributionReviewManager.hasEditor(): %>
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
    <% end %>
    <% else: %>
    <tr>
        <td colspan="5">
            <%= _("The reviewing mode does not allow editing.")%>
        </td>
    </tr>
    <% end %>
</table>



<!-- Assign / remove content reviewers -->

<table width="90%%" align="center" border="0" style="margin-bottom: 1em">
    <tr>
        <td id="assignReviewersHelp" colspan="5" class="groupTitle" style="border: none; padding-bottom:10px;"><%= _("Assign Content Reviewers")%></td>
    </tr>
    <% if ConferenceChoice == 2 or ConferenceChoice == 4: %>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Assigned content reviewers")%></span></td>
            
            <% if not ContributionReviewManager.hasReviewers(): %>
                <td width="60%%" class='bottom_line'>
                    <%= _("No content reviewers assigned to this contribution.")%>
                </td>
            <% end %>
            <% else: %>
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
                <td align="right">
                    <input type="submit" class=btn value="remove">
                </td>
    			</form>
            <% end %>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Assign content reviewers to this contribution")%></span>
            </td>
            <form action="<%=assignReviewingURL%>" method="post">
            <% showAssignButton = False %>
            <td width="80%%"  class='bottom_line'>
                <% if CanAssignEditorOrReviewers: %>
                    <% if len(ConfReview.getReviewersList()) == 0: %>
                        <%= _("No reviewers proposed for this conference.")%>
                    <% end %>
                    <% elif not ContributionReviewManager.hasReferee(): %>
                        <%= _("Please choose a referee first.")%>
                    <% end %>
    				<% elif len(AvailableReviewers) == 0: %>
    				    <%= _("No more reviewers available in this conference.")%>
    				<% end %>
                    <% else: %>
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
                <td align="right">
                    <input type="submit" class=btn value="assign">
                </td>
            <% end %>
            </form>
        </tr>
        <% if ContributionReviewManager.hasReviewers(): %>
            <tr>
                <td class="dataCaptionTD">
                    <span class="dataCaptionFormat"><%= _("Deadline")%></span>
                </td>
                <td class="blacktext">
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
    <% end %>
    <% else: %>
    <tr>
        <td colspan="5">
            <%= _("The reviewing mode does not allow content reviewing.")%>
        </td>
    </tr>
    <% end %>
</table>





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