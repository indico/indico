<% declareTemplate(newTemplateStyle=True) %>
<% from MaKaC.reviewing import ConferenceReview %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.utils import formatDateTime %>

<% format = "%a %d %b %Y at %H\x3a%M" %>



<!-- Judgement of the editor -->
<table width="90%%" align="center" border="0" style="margin-bottom: 1em; margin-top: 1em">
    <tr>
        <td id="editingJudgementHelp" colspan="5" class="groupTitle" style="border-bottom: none"><%= _("Layout judgement details")%>
            <% inlineContextHelp(_('Here is displayed the judgement given by the Layout Reviewer.<br/>Only the Layout Reviewer of this contribution can change this.')) %>
        </td>
    </tr>
    <tr>
        <td align="left">
            <% if ConferenceChoice == 3 or ConferenceChoice == 4: %>
                <% if Editing.isSubmitted(): %>
                    <% includeTpl ('EditingJudgementDisplay', Editing = Editing, ShowEditor = True) %>
                <% end %>
                <% else: %>
                    <font><%= _("Warning: the layout reviewer has not given his judgement yet.")%></span> 
                <% end %>
            <% end %>
            <% else: %>
                <%= _("The conference review mode does not allow layout editing.")%>
            <% end %>
        </td>
    </tr>
</table>

<!-- List of advices from the reviewers -->
<table width="90%%" align="center" border="0" style="margin-bottom: 1em">
    <tr>
        <td id="reviewingJudgementHelp" colspan="5" class="groupTitle" style="padding-top: 5px; border-bottom: none"><%= _("Content judgement details")%>
            <% inlineContextHelp(_('Here is displayed the judgement given by the Content Reviewers<br/>Only the Content Reviewers of this contribution can change their respective judgements.')) %>
        </td>
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
                    <font><%= _("Warning: all your content reviewers have not given their advices yet.")%></span>
                <% end %>
            <% end %>
            <% else: %>
                <%= _("This conference does not enable content reviewing. The layout reviewer's judgement is the only judgement.")%>
            <% end %>
        </td>
    </tr>
</table>



<!-- Final reviewing of the referee -->
<table width="90%%" align="center" border="0" style="margin-bottom: 1em">
    <tr>
        <td id="finalJudgementHelp" colspan="5" class="groupTitle" style="padding-bottom: 15px; padding-top: 5px; border-bottom: none"><a name="FinalReviewing"></a><%= _("Final Judgement")%>
            <% inlineContextHelp(_('Here is displayed the judgement given by the Referee.<br/>If you are the Referee of this contribution, you can change this.')) %>    
        </td>
    </tr>
    <% if not (ConferenceChoice == 2 or ConferenceChoice == 4): %>
    <tr>
        <td colspan="2" align="left">
            <span><%= _("This conference does not enable content reviewing. The layout reviewer's judgement is the only judgement.")%></span>
        </td>
    </tr>
    <% end %>
    <% else: %>
        <% if IsReferee: %>
            <% if not Review.isAuthorSubmitted(): %>
                <tr>
                    <td colspan="2" align="left">
                        <span>
                            <%= _("The author has not submitted the materials yet.")%><br>
                            <%= _("Please wait until he/she does so.")%>
                        </span>
                    </td>
                </tr>
            <% end %>
            <% else: %>
                <% if ConferenceChoice == 4 and not Editing.isSubmitted(): %>
                   <tr>
                       <td colspan="2" align="left">
                           <font><%= _("Warning: the layout reviewer has not given his judgement yet.")%></span> 
                       </td>
                   </tr>
                <% end %>
                <% if (ConferenceChoice == 2 or ConferenceChoice == 4) and not Review.allReviewersHaveGivenAdvice(): %>
                   <tr>
                       <td colspan="2" align="left">
                           <font><%= _("Warning: all your content reviewers have not given their advices yet.")%></span>
                       </td>
                   </tr>
                <% end %>
            <% end %>
        <% end %>
        <% else: %>
            <% if not Review.getRefereeJudgement().isSubmitted(): %>
                <tr>
                    <td colspan="2" align="center">
                        <span>
                        <%= _("This contribution has not been judged yet.")%><br>
                        <%= _("You are not allowed to perform the final judgement on this contribution.")%>
                        </span>
                    </td>
                </tr>
            <% end %>
        <% end %>
        
        <tr>
            <td nowrap class="titleCellTD" style="padding-top: 10px;"><span class="titleCellFormat"><strong><%= _("Judgement")%>:</strong></span></td>
            <td style="padding-top: 10px;">
                <div id="inPlaceEditJudgement"><strong><%= Review.getRefereeJudgement().getJudgement() %></strong></div>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Reviewing questions:")%></span>
            </td>
            <td width="60%%" id="questionListDisplay">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Comments")%>:</span></td>
            <td>
                <div id="inPlaceEditComments"></div>
            </td>
        </tr>
        <% if IsReferee: %>
        <% if not FinalJudge: %>
        <% display = 'span' %>
		<% end %>
		<% else: %>
		    <% display = 'none' %>
		<% end %>
        <tr>
            <td colspan="3" style="padding-top: 20px">
                <span id="submitbutton" align="right"></span>
                <span id="submitHelpPopUp" style="display:<%=display%>" align="right"></span>
                <span id="submittedmessage"></span>
            </td>
        </tr>
        <% end %>
    <% end %>                    
                        
</table>

<script type="text/javascript">

var observer = function(value) {
                if(value!="None"){
                        submitButton.dom.disabled = false;
                        $E('submitHelpPopUp').set("");
                        $E('submitHelpPopUp').dom.display = 'none';
                        }
                     
}
               
var showWidgets = function(firstLoad) {
                           
    new IndicoUI.Widgets.Generic.selectionField($E('inPlaceEditJudgement'),
                        'reviewing.contribution.changeJudgement',
                        {conference: '<%= Contribution.getConference().getId() %>',
                        contribution: '<%= Contribution.getId() %>',
                        current: 'refereeJudgement'
                        }, <%= ConfReview.getAllStates() %>, "<%=FinalJudge%>", observer);       
    
    new IndicoUI.Widgets.Generic.richTextField($E('inPlaceEditComments'),
                           'reviewing.contribution.changeComments',
                           {conference: '<%= Contribution.getConference().getId() %>',
                            contribution: '<%= Contribution.getId() %>',
                            current: 'refereeJudgement'
                           },400,200);
                           
    
    
    <% if len (ConfReview.getReviewingQuestions()) == 0 : %>
        $E('questionListDisplay').set($T("No reviewing questions proposed for this conference."));
    <% end %>
    <% else: %>
        $E("questionListDisplay").set('');
        <% for q in ConfReview.getReviewingQuestions(): %>
            var newDiv = Html.div({style:{paddingLeft:'5px', marginLeft:'10px'}});
            
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
                    $E('inPlaceEditJudgement').set(result);
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
                        $E('questionListDisplay').set($T('No reviewing questions proposed for this conference.'));
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
        submitButton.set($T('Undo sending'));
        $E('submittedmessage').set($T('Judgement has been sent'));
        <% end %>
        showValues();
    } else {
        <% if IsReferee: %>
        submitButton.set($T('Send'));
        <% if not Review.isAuthorSubmitted() or not FinalJudge: %>
            submitButton.dom.disabled = true;
            var HelpImg = Html.img({src: '<%= Config.getInstance().getSystemIconURL("help") %>', style: {marginLeft: '5px', verticalAlign: 'middle'}});
            $E('submitHelpPopUp').append(HelpImg);
            <% if not Review.isAuthorSubmitted(): %>
		            var submitHelpPopUpText = function(event) {
		              IndicoUI.Widgets.Generic.tooltip(this, event, "<span style='padding:3px'>You are not allowed to give final judgement.<br/>You have to wait for the author to submit the materials.</span>");
		                } 
		    <% end %>
		    <% if not FinalJudge: %>
	               var submitHelpPopUpText = function(event) {
                      IndicoUI.Widgets.Generic.tooltip(this, event, "<span style='padding:3px'>You must give your judgement before sending.</span>");
                        } 	        
		    <% end %>
            $E('submitHelpPopUp').dom.onmouseover = submitHelpPopUpText;
        <% end %>        
        $E('submittedmessage').set($T('Judgement not sent yet'));
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
        $T('Send')
);
<% end %>

updatePage(true);                   
                   
</script>