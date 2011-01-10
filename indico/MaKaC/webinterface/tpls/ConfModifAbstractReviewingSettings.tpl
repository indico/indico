<!-- The date is not necessary yet because now the reviewing stops when
     the call for abstracts is disable -->
<!--
<table width="90%%" border="0" style="padding-bottom: 10px;">
    <tr>
        <td id="reviewingModeHelp" colspan="5" class="groupTitle" style="padding-bottom: 10px; padding-left: 20px;">
            <%= _("Default date for abstract reviewing")%>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD" style="padding-left: 30px; padding-top: 15px;"><span class="titleCellFormat">
            <%= _("Abstract Reviewer Deadline")%>
        </span></td>
        <td class="blacktext" style="padding-top: 15px;">
            <span id="inPlaceEditDefaultAbstractReviewerDueDate">
                <% date = abstractReview.getAdjustedDefaultAbstractReviewerDueDate() %>
                <% if date is None: %>
                    <%= _("Date has not been set yet.")%>
                <% end %>
                <% else: %>
                    <%= formatDateTime(date) %>
                <% end %>
            </span>
        </td>
    </tr>
</table>
-->

<table id="reviewingQuestionsTable" width="90%%" border="0" style="padding-bottom: 10px;">
    <tr>
        <td id="reviewingQuestionsHelp" colspan="5" class="groupTitle" style="padding-bottom: 10px;"><%= _("Add questions for abstract reviewing")%></td>
    </tr>
    <tr>
        <td>
            <div id="inPlaceEditQuestions"  style="padding-top: 10px; padding-left: 30px"><%= ', '.join(abstractReview.getReviewingQuestions())%></div>
        </td>
    </tr>
</table>

<table id="reviewingScaleTable" width="90%%" border="0" style="padding-bottom: 10px;">
    <tr>
        <td id="reviewingScale" colspan="5" class="groupTitle" style="padding-bottom: 10px;"><%= _("Add the number of answers per question and the scale for the rating")%>
       <% inlineContextHelp(_('Here you can set the number of answers you wish to have for each question and the scale in which you want to see the abstract rating later. ')) %> </td>
    </tr>
</table>
<table>
    <tr>
        <td style="padding-right:15px;">
            <div style="padding-left: 30px; padding-bottom: 10px;">
                <table>
                    <tr>
                        <td class="reviewingsubtitle">
                            <span><%= _("Select the number of answers per question")%></span>
                            <span><% inlineContextHelp(_('You can select the number of options the reviewers are going to have to answer each question. The minimun is 2 and the maximum 20.')) %></span>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <div id="inPlaceEditNumberOfAnswers" style="padding-left: 25px;"></div>
                        </td>
                    </tr>
                </table>
            </div>

            <div style="padding-left: 30px; padding-bottom: 10px;">
                <table>
                    <tr>
                        <td class="reviewingsubtitle">
                            <span><%= _("Select the scale for the rating")%></span>
                            <span><% inlineContextHelp(_('You can select the range in which you want to have the abstract rating. The maximum difference between the limits can be 100 units and it is possible to have negative numbers.')) %></span>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <div id="inPlaceEditScale" style="padding-left: 25px;"></div>
                        </td>
                    </tr>
                </table>
            </div>
        </td>
        <td valign="top">
            <div class="shadowRectangle">
                <span class="reviewingsubtitle">Preview</span>
                <div id="inPlaceShowExample"></div>
            </div>
        </td>
    </tr>
</table>


<script type="text/javascript">
/*new IndicoUI.Widgets.Generic.dateEditor($E('inPlaceEditDefaultAbstractReviewerDueDate'),
                   'reviewing.conference.changeAbstractReviewerDefaultDueDate',
                   {conference: '<%= abstractReview.getConference().getId() %>',
                    dueDateToChange: '<%= _("Abstract Reviewer")%>'},
                   null, true);*/

// Reviewing questions
var showReviewingQuestions = function() {
    new IndicoUI.Widgets.Generic.keywordField(
        $E('inPlaceEditQuestions'),
        'multipleLinesListItem',
        'reviewing.conference.changeAbstractQuestions',
        {conference: '<%= abstractReview.getConference().getId() %>'},
        $T('Remove this question from the list')
    );
}

showReviewingQuestions();

//get the first question or a default one
var listOfQuestions = <%= abstractReview.getReviewingQuestions() %>;
if (listOfQuestions.length == 0) {
    var question = "Do you like Indico?";
} else {
    var question = listOfQuestions[0];
}

// Component for example question
var previewQuestion =  new ExampleQuestionWidget('reviewing.abstractReviewing.updateExampleQuestion',
        {conference: '<%= abstractReview.getConference().getId() %>'});
previewQuestion.draw();

// Components to change the number of answers and the scale
$E('inPlaceEditNumberOfAnswers').set(new NumberAnswersEditWidget('reviewing.abstractReviewing.changeNumberofAnswers',
       {conference: '<%= abstractReview.getConference().getId() %>'},'<%= abstractReview.getNumberOfAnswers() %>').draw());

$E('inPlaceEditScale').set(new ScaleEditWidget('reviewing.abstractReviewing.changeScale',
       {conference: '<%= abstractReview.getConference().getId() %>'},
       {'min':'<%= abstractReview.getScaleLower() %>', 'max':'<%= abstractReview.getScaleHigher() %>'}).draw());

</script>