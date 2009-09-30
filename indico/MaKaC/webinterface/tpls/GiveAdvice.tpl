<% from MaKaC.reviewing import ConferenceReview %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td colspan="5" class="groupTitle"><%= _("Give opinion on content of a contribution")%></td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Reviewing questions")%></span></td>
        <td width="60%%" id="questionListDisplay">
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Judgement")%></span></td>
        <td>
            <div id="inPlaceEditJudgement"><%= Advice.getJudgement() %></div>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Comments")%></span></td>
        <td>
            <div id="inPlaceEditComments"></div>
            <div id="commentsMessage">
                <%= _("These comments, along with your judgement, will be sent by e-mail to the author(s)")%>
            </div>
        </td>
    </tr>
    <tr>
        <td colspan="10">
            <span id="submitbutton"></span>
            <span id="submittedmessage"></span>
        </td>
    </tr>
</table>


<script type="text/javascript">

var showWidgets = function(firstLoad) {
                           
    new IndicoUI.Widgets.Generic.selectionField($E('inPlaceEditJudgement'),
                        'reviewing.contribution.changeJudgement',
                        {conference: '<%= Contribution.getConference().getId() %>',
                        contribution: '<%= Contribution.getId() %>',
                        current: 'reviewerJudgement'
                        }, <%= ConfReview.getAllStates() %>);
    
    new IndicoUI.Widgets.Generic.richTextField($E('inPlaceEditComments'),
                           'reviewing.contribution.changeComments',
                           {conference: '<%= Contribution.getConference().getId() %>',
                            contribution: '<%= Contribution.getId() %>',
                            current: 'reviewerJudgement'
                           },400,200);
                           
    $E('commentsMessage').set($T('These comments, along with your judgement, will be sent by e-mail to the author(s)'));
    
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
                var initialValue = "<%= Advice.getAnswer(q) %>";
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
                                                    current: 'reviewerJudgement'
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
                current: 'reviewerJudgement'
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
                current: 'reviewerJudgement'
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
                current: 'reviewerJudgement'
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



<% if Advice.isSubmitted():%> 
    var submitted = true;
<% end %>
<% else: %>
    var submitted = false;
<% end %>

var updatePage = function (firstLoad){
    if (submitted) {
        submitButton.set($T('Send submittion'));
        $E('submittedmessage').set($T('Judgement has been send'));
        showValues();
    } else {
        submitButton.set('Mark as submitted');
        $E('submittedmessage').set('Judgement not submitted yet');
        showWidgets(firstLoad);
    }
}

var submitButton = new IndicoUI.Widgets.Generic.simpleButton($E('submitbutton'), 'reviewing.contribution.setSubmitted',
        {
            conference: '<%= Contribution.getConference().getId() %>',
            contribution: '<%= Contribution.getId() %>',
            current: 'reviewerJudgement',
            value: true
        },
        function(result, error){
            if (!error) {
                submitted = !submitted;
                updatePage(false)
            } else {
                alert (error)
            }
        },
        ''
);

updatePage(true);

</script>