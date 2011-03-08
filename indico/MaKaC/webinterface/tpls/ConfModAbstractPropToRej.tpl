<% from MaKaC.common.fossilize import fossilize %>

<form action=${ postURL } method="POST" onsubmit="return checkQuestionsAnswered();">
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

var questionPM = new IndicoUtil.parameterManager();

var showQuestions = function() {

    var numQuestions = ${ len(abstractReview.getReviewingQuestions()) };
    var newDiv;
    var reviewingQuestions = ${ fossilize(abstractReview.getReviewingQuestions()) };
    var range = ${ str(range(abstractReview.getNumberOfAnswers())) };
    var labels = ${ str(abstractReview.getRBLabels()) };

    $E("questionListDisplay").set('');
    for (var i=0; i<numQuestions; i++) {
        newDiv = Html.div({style:{marginLeft:'10px'}});
        newDiv.append(Html.span(null, reviewingQuestions[i].text));
        newDiv.append(Html.br());

        var rbsf = new RadioButtonSimpleField(null, range, labels);
        rbsf.plugParameterManager(questionPM);
        newDiv.append(rbsf.draw());

        $E("questionListDisplay").append(newDiv);
        $E("questionListDisplay").append(Html.br());
    }

    var numAnswers = ${ abstractReview.getNumberOfAnswers() };
    var rbValues = ${ str(abstractReview.getRBTitles()) };
    var groupName = "_GID" // The common name for all the radio buttons

    for (var i=1; i<numQuestions+1; i++) {
        for (var j=0; j<numAnswers; j++) {
            $E(groupName+i + "_" + j).dom.onmouseover = function(event) {
                var value = rbValues[this.defaultValue];
                IndicoUI.Widgets.Generic.tooltip(this, event, "<span style='padding:3px'>"+value+"</span>");
            };
        }
    }

};

var checkQuestionsAnswered = function() {
    if(questionPM.check()) {
        return true;
    }

    alert($T('Please answer all questions.'));
    return false;
};

showQuestions();

</script>
% endif