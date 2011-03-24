<% from MaKaC.common.fossilize import fossilize %>

<form action="${ postURL }" method="POST" onsubmit="return questionsManager.checkQuestionsAnswered();">
    <table align="left" width="50%" border="0" cellspacing="6" cellpadding="2" style="padding-left:15px;">
        <tr>
            <td class="groupTitle" colspan="2"> ${ _("Propose to be accepted")}</td>
        </tr>
        <tr>
            <td bgcolor="white" colspan="2">
                <font color="#5294CC"> ${ _("Abstract title")}:</font><font color="gray"> ${ abstractTitle }<br></font>
                <font color="#5294CC"> ${ _("Track")}:</font><font color="gray"> ${ trackTitle }</font>
                <br>
                <span style="border-bottom: 1px solid #5294CC; width: 100%">&nbsp;</span>
            </td>
        </tr>
        ${ contribTypes }
        % if len(abstractReview.getReviewingQuestions()) > 0:
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Reviewing questions")}</span></td>
            <td width="60%" id="questionListDisplay">
            </td>
        </tr>
        % endif
        <tr>
            <td nowrap colspan="2"><span class="titleCellFormat"> ${ _("Please enter below a comment which justifies your request")}:</span>
                <table>
                    <tr>
                        <td>
                            <textarea cols="50" rows="5" name="comment"></textarea>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr><td  colspan="2">&nbsp;</td></tr>
        <tr>
            <td class="buttonsSeparator" colspan="2" align="center" style="padding:10px">
                <input type="submit" class="btn" name="OK" value="${ _("submit")}">
                <input type="submit" class="btn" name="CANCEL" onclick="this.form.onsubmit = function(){ return true; };" value="${ _("cancel")}">
            </td>
        </tr>
    </table>
</form>

% if len(abstractReview.getReviewingQuestions()) > 0:
<script type="text/javascript">
// JS vars needed from the server.
var numQuestions = ${ len(abstractReview.getReviewingQuestions()) };
var reviewingQuestions = ${ fossilize(abstractReview.getReviewingQuestions()) };
var range = ${ str(range(abstractReview.getNumberOfAnswers())) };
var labels = ${ str(abstractReview.getRBLabels()) };
var numAnswers = ${ abstractReview.getNumberOfAnswers() };
var rbValues = ${ str(abstractReview.getRBTitles()) };

var divId = 'questionListDisplay';

var questionsManager = new QuestionsManager(divId, numQuestions, reviewingQuestions, range, labels, numAnswers, rbValues);
questionsManager.showQuestions();

</script>
% endif
