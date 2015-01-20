<% from MaKaC.paperReviewing import ConferencePaperReview %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

% if not Review.isAuthorSubmitted():
<table width="90%" align="center" border="0" style="margin-bottom: 1em">
    % if len(Review.getReviewManager().getVersioning()) == 1:
    <tr>
        <td>
            <p style="padding-left: 25px;"><font color="gray">
            ${ _("Warning: the author(s) of this contribution have still not marked their initial materials as submitted.")}<br>
            ${ _("You must wait until then to start the reviewing process.")}
            </font></p>
        </td>
    </tr>
    % else:
    <tr>
        <td>
            <p style="padding-left: 25px;"><font color="gray">
            ${ _("Warning: since this contribution was marked 'To be corrected', the author(s) has not submitted new materials.")}<br>
            ${ _("You must wait until then to restart the reviewing process.")}<br>
            </font></p>
        </td>
    </tr>
    % endif
</table>
% else:
<table width="90%" align="center" border="0" style="padding-top: 15px;">
    <tr>
        <td colspan="5" class="groupTitle" style="border: none">${ _("Give opinion on the content of a contribution")}
            ${inlineContextHelp(_('Here is displayed the assessment given by the Content Reviewers<br/>Only the Content Reviewers of this contribution can change their respective assessments.'))}
        </td>
    </tr>
    % if len (ConfReview.getReviewingQuestions()) > 0 :
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Reviewing questions")}</span></td>
        <td width="60%" id="questionListDisplay">
        </td>
    </tr>
    % endif
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Comments")}</span></td>
        <td>
            <div id="inPlaceEditComments"></div>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Assessment")}</span></td>
        <td>
            <div id="statusDiv">
                <div id="initialStatus" style="display:inline">${ Advice.getJudgement() }</div>
                <div id="inPlaceEditJudgement" style="display:inline"></div>
            </div>
            <div id="commentsMessage" style="padding-top:5px;">
                ${ _("The comments and your assessment, will be sent by e-mail to the author(s)")}
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

var observer = function(value) {
    if($E('initialStatus')) {
        $E('statusDiv').remove($E('initialStatus'));
        submitButton.dom.disabled = false;
    }
}

var showWidgets = function(firstLoad) {

    new IndicoUI.Widgets.Generic.selectionField($E('inPlaceEditJudgement'),
                        'reviewing.contribution.changeJudgement',
                        {conference: '${ Contribution.getConference().getId() }',
                        contribution: '${ Contribution.getId() }',
                        current: 'reviewerJudgement'
                        }, ${ ConfReview.getStatusesDictionary() },
                        "${ Advice.getJudgement() }", observer);

    var initialValue = ${ Advice.getComments() | n,j};
    if (initialValue == '') {
        initialValue = 'No comments';
    }

    $E('inPlaceEditComments').set(new TextAreaEditWidget('reviewing.contribution.changeComments',
            {conference: '${ Contribution.getConference().getId() }',
             contribution: '${ Contribution.getId() }',
             current: 'reviewerJudgement'},initialValue).draw());


    % if len (ConfReview.getReviewingQuestions()) > 0 :
        $E("questionListDisplay").set('');
        % for q in ConfReview.getReviewingQuestions():
            var newDiv = Html.div({style:{borderLeft:'1px solid #777777', paddingLeft:'5px', marginLeft:'10px'}});

            newDiv.append(Html.span(null,${q.getText() | n,j}));
            newDiv.append(Html.br());

            if (firstLoad) {
                % if Advice.getAnswer(q.getId()) is None:
                    var initialValue = "${ Advice.createAnswer(q.getId()).getRbValue() }";
                % else:
                    var initialValue = "${ Advice.getAnswer(q.getId()).getRbValue() }";
                % endif
            } else {
                var initialValue = false;
            }

            newDiv.append(new IndicoUI.Widgets.Generic.radioButtonField(
                                                    null,
                                                    'horizontal2',
                                                    ${ str(range(len(ConfReview.reviewingQuestionsAnswers))) },
                                                    ${ str(ConfReview.reviewingQuestionsLabels) },
                                                    initialValue,
                                                    'reviewing.contribution.changeCriteria',
                                                    {conference: '${ Contribution.getConference().getId() }',
                                                    contribution: '${ Contribution.getId() }',
                                                    criterion: '${ q.getId() }',
                                                    current: 'reviewerJudgement'
                                                    }));

            $E("questionListDisplay").append(newDiv);
            $E("questionListDisplay").append(Html.br());

        % endfor
    % endif
}

var showValues = function() {
    indicoRequest('reviewing.contribution.changeComments',
            {
                conference: '${ Contribution.getConference().getId() }',
                contribution: '${ Contribution.getId() }',
                current: 'reviewerJudgement'
            },
            function(result, error){
                if (!error) {
                    if(result.length == 0){
                        $E('inPlaceEditComments').set($T('No comments given.'));
                    } else {
                        $E('inPlaceEditComments').set(result)
                    }
                }
            }
        )
    indicoRequest('reviewing.contribution.changeJudgement',
            {
                conference: '${ Contribution.getConference().getId() }',
                contribution: '${ Contribution.getId() }',
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
                conference: '${ Contribution.getConference().getId() }',
                contribution: '${ Contribution.getId() }',
                current: 'reviewerJudgement'
            },
            function(result, error){
                if (!error) {
                    if (result.length > 0) {
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



% if Advice.isSubmitted():
    var submitted = true;
% else:
    var submitted = false;
% endif

var updatePage = function (firstLoad){
    if (submitted) {
        if($E('initialStatus')) {
            $E('statusDiv').remove($E('initialStatus'));
        }
        submitButton.set($T('Modify assessment'));
        $E('submittedmessage').set($T('Assessment has been submitted'));
        showValues();
    } else {
        if ("${ Advice.getJudgement() }" == "None") {
            submitButton.dom.disabled = true;
        }
        submitButton.set('Submit');
        $E('submittedmessage').set('Assessment not yet submitted');
        showWidgets(firstLoad);
    }
}

var submitButton = new IndicoUI.Widgets.Generic.simpleButton($E('submitbutton'), 'reviewing.contribution.setSubmitted',
        {
            conference: '${ Contribution.getConference().getId() }',
            contribution: '${ Contribution.getId() }',
            current: 'reviewerJudgement',
            value: true
        },
        function(result, error){
            if (!error) {
                submitted = !submitted;
                //updatePage(false);
                location.href = "${ urlHandlers.UHContributionModifReviewing.getURL(Contribution) }";
                location.reload(true);
            } else {
                new AlertPopup($T("Error"), error.message).open();
                //IndicoUtil.errorReport(error);
            }
        },
        ''
);

updatePage(true);

</script>
% endif
