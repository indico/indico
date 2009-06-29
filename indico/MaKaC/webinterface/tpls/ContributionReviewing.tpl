<% declareTemplate(newTemplateStyle=True) %>
<% from MaKaC.reviewing import ConferenceReview %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.utils import formatDateTime %>

<% format = "%a %d %b %Y at %H\x3a%M" %>


<% if not Review.isAuthorSubmitted(): %>
<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom: 1em">
    <% if len(Review.getReviewManager().getVersioning()) == 1: %>
    <tr>
        <td>
            <span style="color:red;">
            <%= _("Warning: the author(s) of this contribution have still not marked their initial materials as submitted.")%><br>
            The referee, editor and reviewers will receive an email when they do so.<br>
            You must wait until then to start the reviewing process.
            </span>
        </td>
    </tr>
    <% end %>
    <% else: %>
    <tr>
        <td>
            <span style="color:red;">
            Warning: since this contribution was marked 'To be corrected', the author(s) has not submitted new materials.<br>
            The referee, editor and reviewers will receive an email when they do so.
            You must wait until then to restart the reviewing process.<br>
            </span>
        </td>
    </tr>
    <% end %>
</table>
<% end %>

<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom: 1em">
    <!-- Assign or remove a referee -->
    <tr>
        <td id="assignRefereeHelp" colspan="5" class="groupTitle">Assign a referee</td>
    </tr>
    <% if ConferenceChoice == 2 or ConferenceChoice == 4: %>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat">Assigned referee</span>
            </td>
            <% if not ContributionReviewManager.hasReferee(): %>
            <td width="60%%">
                No referee assigned to this contribution.
            </td>
            <% end %>
            <% else: %>
            <td width="60%%">
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
                <span class="titleCellFormat">Assign a referee to this contribution</span>
            </td>
            <form action="<%=assignRefereeURL%>" method="post">
            <% showAssignButton = False %>
            <td width="80%%">
                <% if CanAssignReferee: %>
                    <% if len(ConfReview.getRefereesList()) == 0: %>
                        No referees proposed for this conference.
                    <% end %>
                    <% elif ContributionReviewManager.hasReferee(): %>
                        You can only add one referee for a given contribution.
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
                    You are not allowed to assign referees to this contribution.
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
                <span class="dataCaptionFormat">Due date</span>
            </td>
            <td class="blacktext">
                <span id="inPlaceEditRefereeDueDate">
                    <% date = ContributionReviewManager.getLastReview().getAdjustedRefereeDueDate() %>
                    <% if date is None: %>
                        Date not set yet.
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
            This conference does not enable content reviewing. The editor's judgement is the only judgement.
        </td>
    </tr>
    <% end %>
</table>

<!-- Assign / remove Editors -->
<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom: 1em">
    <tr>
        <td id="assignEditorHelp" colspan="5" class="groupTitle">Assign an Editor</td>
    </tr>
    <% if ConferenceChoice == 3 or ConferenceChoice == 4: %>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">Assigned editor</span></td>
        
        <% if not ContributionReviewManager.hasEditor(): %>
            <td width="60%%">
                No editor assigned to this contribution.
            </td>
            <% end %>
            <% else: %>
            <td width="60%%">
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
            <span class="titleCellFormat">Assign an editor to this contribution</span>
        </td>
        <form action="<%=assignEditingURL%>" method="post">
        <% showAssignButton = False %>
        <td width="80%%">
            <% if CanAssignEditorOrReviewers: %>
                <% if len(ConfReview.getEditorsList()) == 0: %>
                    No editors proposed for this conference.
                <% end %>
                <% elif ContributionReviewManager.hasEditor(): %>
                    You can only add one editor for a given contribution.
                <% end %>
                <% elif not ContributionReviewManager.hasReferee() and not ConferenceChoice == 3: %>
                    Please choose a referee first.
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
                You are not allowed to assign editors to this contribution.
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
                <span class="dataCaptionFormat">Due date</span>
            </td>
            <td class="blacktext">
                <span id="inPlaceEditEditorDueDate">
                    <% date = ContributionReviewManager.getLastReview().getAdjustedEditorDueDate() %>
                    <% if date is None: %>
                        Date not set yet.
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
            The reviewing mode does not allow editing.
        </td>
    </tr>
    <% end %>
</table>



<!-- Assign / remove content reviewers -->

<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom: 1em">
    <tr>
        <td id="assignReviewersHelp" colspan="5" class="groupTitle">Assign Reviewers</td>
    </tr>
    <% if ConferenceChoice == 2 or ConferenceChoice == 4: %>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Assigned reviewers</span></td>
            
            <% if not ContributionReviewManager.hasReviewers(): %>
                <td width="60%%">
                    No content reviewers assigned to this contribution.
                </td>
            <% end %>
            <% else: %>
    			<form action="<%=removeAssignReviewingURL%>" method="post">
                <td width="60%%">
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
                <span class="titleCellFormat">Assign reviewers to this contribution</span>
            </td>
            <form action="<%=assignReviewingURL%>" method="post">
            <% showAssignButton = False %>
            <td width="80%%">
                <% if CanAssignEditorOrReviewers: %>
                    <% if len(ConfReview.getReviewersList()) == 0: %>
                        No reviewers proposed for this conference.
                    <% end %>
                    <% elif not ContributionReviewManager.hasReferee(): %>
                        Please choose a referee first.
                    <% end %>
    				<% elif len(AvailableReviewers) == 0: %>
    				    No more reviewers available in this conference.
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
                    You are not allowed to assign reviewers to this contribution.
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
                    <span class="dataCaptionFormat">Due date</span>
                </td>
                <td class="blacktext">
                    <span id="inPlaceEditReviewerDueDate">
                    <% date = ContributionReviewManager.getLastReview().getAdjustedReviewerDueDate() %>
                    <% if date is None: %>
                        Date not set yet.
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
            The reviewing mode does not allow content reviewing.
        </td>
    </tr>
    <% end %>
</table>



<!-- Judgement of the editor -->
<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom: 1em; margin-top: 1em">
    <tr>
        <td id="editingJudgementHelp" colspan="5" class="groupTitle">Editing judgement</td>
    </tr>
	<tr>
		<td>
            <% if ConferenceChoice == 3 or ConferenceChoice == 4: %>
                <% if Editing.isSubmitted(): %>
                    <% includeTpl ('EditingJudgementDisplay', Editing = Editing, ShowEditor = True) %>
                <% end %>
                <% else: %>
                    <font color="red">Warning: the editor has not given his judgement yet.</span> 
                <% end %>
            <% end %>
            <% else: %>
                The conference review mode does not allow layout editing.
            <% end %>
        </td>
    </tr>
</table>

<!-- List of advices from the reviewers -->
<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom: 1em">
    <tr>
        <td id="reviewingJudgementHelp" colspan="5" class="groupTitle">Reviewing judgement</td>
    </tr>
    <tr>
        <td>
            <% if ConferenceChoice == 2 or ConferenceChoice == 4: %>
                <% if len(AdviceList) > 0: %>
                    <table cellspacing="0" cellpadding="5" width="100%%">
                    <% for advice in AdviceList: %>
                        <% includeTpl ('AdviceJudgementDisplay', advice = advice, ShowReviewer = True) %>
                    <% end %>
                    </table>
                <% end %>
                <% else: %>
                    <font color="red">Warning: all your reviewers have not given their advices yet.</span>
                <% end %>
            <% end %>
            <% else: %>
                This conference does not enable content reviewing. The editor's judgement is the only judgement.
            <% end %>
        </td>
    </tr>
</table>



<!-- Final reviewing of the referee -->
<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom: 1em">
    <tr>
        <td id="finalJudgementHelp" colspan="5" class="groupTitle"><a name="FinalReviewing"></a>Final Judgement</td>
    </tr>
    <% if not (ConferenceChoice == 2 or ConferenceChoice == 4): %>
    <tr>
        <td colspan="2" align="center">
            <span style="color:red;">This conference does not enable content reviewing. The editor's judgement is the only judgement.</span>
        </td>
    </tr>
    <% end %>
    <% else: %>
        <% if IsReferee: %>
            <% if not Review.isAuthorSubmitted(): %>
                <tr>
                    <td colspan="2" align="center">
                        <span style="color:red;">
                            The author has not submitted the materials yet.<br>
                            Please wait until he/she does so.
                        </span>
                    </td>
                </tr>
            <% end %>
            <% else: %>
                <% if ConferenceChoice == 4 and not Editing.isSubmitted(): %>
                   <tr>
                       <td colspan="2" align="center">
                           <font color="red">Warning: the editor has not given his judgement yet.</span> 
                       </td>
                   </tr>
                <% end %>
                <% if (ConferenceChoice == 2 or ConferenceChoice == 4) and not Review.allReviewersHaveGivenAdvice(): %>
                   <tr>
                       <td colspan="2" align="center">
                           <font color="red">Warning: all your reviewers have not given their advices yet.</span>
                       </td>
                   </tr>
                <% end %>
            <% end %>
        <% end %>
        <% else: %>
            <% if not Review.getRefereeJudgement().isSubmitted(): %>
                <tr>
                    <td colspan="2" align="center">
                        <span style="color:red;">
                        This contribution has not been judged yet.<br>
                        You are not allowed to perform the final judgement on this contribution.
                        </span>
                    </td>
                </tr>
            <% end %>
        <% end %>
        
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat">Reviewing questions</span>
            </td>
            <td width="60%%" id="questionListDisplay">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Judgement</span></td>
            <td>
                <div id="inPlaceEditJudgement"><%= Review.getRefereeJudgement().getJudgement() %></div>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Comments</span></td>
            <td>
                <div id="inPlaceEditComments"></div>
                <div id="commentsMessage">
                    These comments, along with your judgement, will be sent by e-mail to the author(s)
                </div>
            </td>
        </tr>
        <% if IsReferee: %>
        <tr>
            <td colspan="10">
                <span id="submitbutton"></span>
                <span id="submittedmessage"></span>
            </td>
        </tr>
        <% end %>
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
                   
var showWidgets = function(firstLoad) {
                           
    new IndicoUI.Widgets.Generic.selectionField($E('inPlaceEditJudgement'),
                        'reviewing.contribution.changeJudgement',
                        {conference: '<%= Contribution.getConference().getId() %>',
                        contribution: '<%= Contribution.getId() %>',
                        current: 'refereeJudgement'
                        }, <%= ConfReview.getAllStates() %>);
    
    new IndicoUI.Widgets.Generic.richTextField($E('inPlaceEditComments'),
                           'reviewing.contribution.changeComments',
                           {conference: '<%= Contribution.getConference().getId() %>',
                            contribution: '<%= Contribution.getId() %>',
                            current: 'refereeJudgement'
                           },400,200);
                           
    $E('commentsMessage').set('These comments, along with your judgement, will be sent by e-mail to the author(s)')
    
    <% if len (ConfReview.getReviewingQuestions()) == 0 : %>
        $E('questionListDisplay').set("No reviewing questions proposed for this conference.");
    <% end %>
    <% else: %>
        $E("questionListDisplay").set('');
        <% for q in ConfReview.getReviewingQuestions(): %>
            var newDiv = Html.div({style:{borderLeft:'1px solid #777777', paddingLeft:'5px', marginLeft:'10px'}});
            
            newDiv.append(Html.span(null,"<%=q%>"));
            newDiv.append(Html.br());
                        
            if (firstLoad) {
                var initialValue = "<%= Review.getRefereeJudgement().getAnswer(q) %>";
            } else {
                var initialValue = false;
            }
            
            newDiv.append(new IndicoUI.Widgets.Generic.radioButtonField(
                                                    null,
                                                    'horizontal2',
                                                    <%= str(range(len(ConfReview.reviewingQuestionsAnswers))) %>,
                                                    <%= str(ConfReview.reviewingQuestionsLabels) %>,
                                                    initialValue,
                                                    'reviewing.contribution.changeCriteria', 
                                                    {conference: '<%= Contribution.getConference().getId() %>',
                                                    contribution: '<%= Contribution.getId() %>',
                                                    criterion: '<%= q %>',
                                                    current: 'refereeJudgement'
                                                    }));
            
            $E("questionListDisplay").append(newDiv);
            $E("questionListDisplay").append(Html.br());
            
        <% end %>
    <% end %>
}

var showValues = function() {
    indicoRequest('reviewing.contribution.changeComments',
            {
                conference: '<%= Contribution.getConference().getId() %>',
                contribution: '<%= Contribution.getId() %>',
                current: 'refereeJudgement'
            },
            function(result, error){
                if (!error) {
                    $E('inPlaceEditComments').set(result)
                    $E('commentsMessage').set('')
                }
            }
        )
    indicoRequest('reviewing.contribution.changeJudgement',
            {
                conference: '<%= Contribution.getConference().getId() %>',
                contribution: '<%= Contribution.getId() %>',
                current: 'refereeJudgement'
            },
            function(result, error){
                if (!error) {
                    $E('inPlaceEditJudgement').set(result)
                }
            }
        )
    
    indicoRequest('reviewing.contribution.getCriteria',
            {
                conference: '<%= Contribution.getConference().getId() %>',
                contribution: '<%= Contribution.getId() %>',
                current: 'refereeJudgement'
            },
            function(result, error){
                if (!error) {
                    if (result.length == 0) {
                        $E('questionListDisplay').set('No reviewing questions proposed for this conference.');
                    } else {
                        $E('questionListDisplay').set('');
                        for (var i = 0; i<result.length; i++) {
                            $E('questionListDisplay').append(result[i]);
                            $E('questionListDisplay').append(Html.br());
                        }
                    }

                }
            }
        )   
}


<% if Review.getRefereeJudgement().isSubmitted() or not IsReferee:%> 
var submitted = true;
<% end %>
<% else: %>
var submitted = false;
<% end %>


var updatePage = function (){
    if (submitted) {
        <% if IsReferee: %>
        submitButton.set('Mark as NOT submitted');
        $E('submittedmessage').set('Judgement submitted');
        <% end %>
        showValues();
    } else {
        <% if IsReferee: %>
        submitButton.set('Mark as submitted');
        $E('submittedmessage').set('Judgement not submitted yet');
        <% end %>
        showWidgets();
    }
}

<% if IsReferee: %>
var submitButton = new IndicoUI.Widgets.Generic.simpleButton($E('submitbutton'), 'reviewing.contribution.setSubmitted',
        {
            conference: '<%= Contribution.getConference().getId() %>',
            contribution: '<%= Contribution.getId() %>',
            current: 'refereeJudgement',
            value: true
        },
        function(result, error){
            if (!error) {
                submitted = !submitted;
                /*updatePage(false)*/
                location.href = "<%= urlHandlers.UHContributionModifReviewing.getURL(Contribution) %>#FinalReviewing"
                location.reload(true)
            } else {
                IndicoUtil.errorReport(error);
            }
        },
        'Mark as submitted'
);
<% end %>

updatePage(true);                   
                   
</script>