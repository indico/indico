<% from MaKaC.common import Config %>
<table id="reviewingQuestionsTable" width="90%" border="0" style="padding-bottom: 5px;">
    <tr>
        <td id="reviewingQuestionsHelp" colspan="5" class="groupTitle">${ _("Reviewing questions")}</td>
    </tr>
</table>
<table style="padding-left: 20px;">
    <tr>
        <td class="subGroupTitle" colspan="3">${ _("Add the questions that the abstract reviewers must answer")}
        ${inlineContextHelp(_('The questions you add here will be shown to the reviewers when they propose to accept/reject an abstract.'))}
</td>
    </tr>
    <tr>
        <td>
            <div id="inPlaceEditQuestions"></div>
        </td>
    </tr>
</table>
<table style="padding-left: 20px; padding-top: 20px;">
    <tr>
        <td class="subGroupTitle" colspan="2">${ _("Answers setup")}
        ${inlineContextHelp(_('Here you can set the number of answers you wish to have for each question and the scale in which you want to see the abstract rating later. The number of answers must be a number between 2 and 20. For the scale, the maximum difference between the limits can be 100 units and it is possible to have negative numbers.'))}
        </td>
    </tr>
    <tr>
        <td valign="top">
            <div id="inPlaceEditNumberOfAnswers" ></div>
        </td>
        <td rowspan="2" valign="top" style="padding-top:10px;">
            <div class="shadowRectangle">
                <span class="reviewingsubtitle">Preview</span>
                <div id="inPlaceShowExample"></div>
            </div>
        </td>
    </tr>
    <tr>
        <td valign="top">
            <div id="inPlaceEditScale"></div>
        </td>
    </tr>
</table>
<table id="reviewingQuestionsTable" width="90%" border="0" style="padding-bottom: 5px;">
    <tr>
        <td colspan="5" class="groupTitle">${ _("Reviewer rights")}</td>
    </tr>
</table>
<table>
  <tr>
    <td style="padding-left:25px;">
        <div id="inPlaceAllowAccept"></div>
    </td>
  </tr>
</table>

<script type="text/javascript">
// Component for the review questions
$('#inPlaceEditQuestions').html(new ManageListOfElements({'get':'abstractReviewing.questions.getQuestions',
        'add':'abstractReviewing.questions.addQuestion', 'remove':'abstractReviewing.questions.removeQuestion',
        'edit': 'abstractReviewing.questions.editQuestion'},
        {conference: '${ abstractReview.getConference().getId() }'},'question', 'abstractReviewingQuestions', true).draw().dom);


//get the first question or a default one
var question = "How would you rate this abstract?";

// Component for example question
var previewQuestion =  new ExampleQuestionWidget('abstractReviewing.questions.updateExampleQuestion',
        {conference: '${ abstractReview.getConference().getId() }'}, 'inPlaceShowExample');
previewQuestion.draw();

// Components to change the number of answers and the scale
$('#inPlaceEditNumberOfAnswers').html(new NumberAnswersEditWidget('abstractReviewing.questions.changeNumberofAnswers',
       {conference: '${ abstractReview.getConference().getId() }'},'${ abstractReview.getNumberOfAnswers() }').draw().dom);

$('#inPlaceEditScale').html(new ScaleEditWidget('abstractReviewing.questions.changeScale',
       {conference: '${ abstractReview.getConference().getId() }'},
       {'min':'${ abstractReview.getScaleLower() }', 'max':'${ abstractReview.getScaleHigher() }'}).draw().dom);



$('#inPlaceAllowAccept').html(new SwitchOptionButton('abstractReviewing.settings.changeReviewerRights', {conference: '${ abstractReview.getConference().getId() }'}, $T("Allow reviewers to accept/reject abstracts"), $T("Saved"), null, false).draw());

</script>
