<% from MaKaC.common.fossilize import fossilize %>

<form action=${ postURL } method="POST" onsubmit="return questionsManager.checkQuestionsAnswered();">
    <table width="60%" align="left" border="0" cellspacing="6" cellpadding="2" style="padding-top:15px; padding-left:15px;">
        <tr>
            <td class="groupTitle" colspan="2"> ${ _("Propose to be rejected")}</td>
        </tr>
        % if len(tracks) > 0:
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> ${ _("Proposed track")}</span>
            </td>
            <td><select name="track">${ tracks }</select></td>
        </tr>
        % else:
        <tr>
            <td colspan="2">
                <span class="titleCellFormat"> <b>${ _("This abstract has not been included in any track, if you want to include it now click")} <a href=${ changeTrackURL }>${ _("here")}</a></b> </span>
            </td>
        </tr>
        % endif
        % if len(abstractReview.getReviewingQuestions()) > 0:
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Reviewing questions")}</span></td>
            <td width="60%" id="questionListDisplay">
            </td>
        </tr>
        % endif
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> ${ _("Comment")}</span>
            </td>
            <td>
                <textarea cols="60" rows="5" name="comment">${ comment }</textarea>
            </td>
        </tr>
        <tr>
            <td colspan="2">&nbsp;</td>
        </tr>
        <tr>
            <td colspan="2" style="text-align: center;">
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
