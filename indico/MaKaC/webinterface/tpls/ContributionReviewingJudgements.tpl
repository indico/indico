<% from MaKaC.paperReviewing import ConferencePaperReview %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.utils import formatDateTime %>

<% format = "%a %d %b %Y at %H\x3a%M" %>


<div style="padding-left: 10px; padding-top: 10px; padding-bottom: 10px;">
<em>${ _("The reviewing mode chosen for this conference is")}: ${ ConferenceChoiceStr}</em>
</div>
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
<!-- Judgement of the editor -->

<table width="90%" align="center" border="0" style="margin-bottom: 1em; margin-top: 1em">

% if ConferenceChoice == 3 or ConferenceChoice == 4:
<tr><td>
<table width="100%" align="center" border="0" style="margin-bottom: 1em; margin-top: 1em">
    <tr>
        <td id="editingJudgementHelp" colspan="5" class="groupTitle" style="border-bottom: none">${ _("Layout assessment details")}
            ${inlineContextHelp(_('Here is displayed the assessment given by the Layout Reviewer.<br/>Only the Layout Reviewer of this contribution can change this.'))}
        </td>
    </tr>
    <tr>
        <td align="left">
                % if Editing.isSubmitted():
                    <%include file="EditingJudgementDisplay.tpl" args="Editing = Editing, ShowEditor = True, format=format, showTitle=False"/>
                % else:
                    <span>${ _("Warning: the layout reviewer has not given his assessment yet.")}</span>
                % endif
        </td>
    </tr>
</table>
</td></tr>
% endif

<!-- List of advices from the reviewers -->
% if ConferenceChoice == 2 or ConferenceChoice == 4:
<tr><td>
<table width="100%" align="center" border="0" style="margin-bottom: 1em">
    <tr>
        <td id="reviewingJudgementHelp" colspan="5" class="groupTitle" style="padding-top: 5px; border-bottom: none">${ _("Content assessment details")}
            ${inlineContextHelp(_('Here is displayed the assessment given by the Content Reviewers<br/>Only the Content Reviewers of this contribution can change their respective assessments.'))}
        </td>
    </tr>
    <tr>
        <td>
                % if len(AdviceList) > 0:
                    <table cellspacing="0" cellpadding="5" width="100%">
                    % for advice in AdviceList:
                    <tr><td>
                        <%include file="AdviceJudgementDisplay.tpl" args="Advice = advice, ShowReviewer = True, format=format, showTitle=False"/>
                    </td></tr>
                    % endfor
                    </table>
                % else:
                    <span>${ _("Warning: all your content reviewers have not given their advices yet.")}</span>
                % endif
        </td>
    </tr>
</table>
</td></tr>
% endif

<!-- Final reviewing of the referee -->
% if ConferenceChoice == 2 or ConferenceChoice == 4:
<tr><td>
<table width="100%" align="center" border="0" style="margin-bottom: 1em">
    <tr>
        <td id="finalJudgementHelp" colspan="5" class="groupTitle" style="padding-bottom: 15px; padding-top: 5px; border-bottom: none; font-weight: bold"><a name="FinalReviewing"></a>${ _("Final Assessment")}
            ${inlineContextHelp(_('Here is displayed the assessment given by the Referee.<br/>If you are the Referee of this contribution, you can change this.'))}
        </td>
    </tr>
        % if Review.getRefereeJudgement().isSubmitted():
             <tr><td>
            <%include file="FinalJudgementDisplay.tpl" args="Review = Review.getRefereeJudgement(), ShowReferee = True, format='%a %d %b %Y at %H\x3a%M', showTitle=False"/>
            </td></tr>
        % else:
            % if not IsReferee:
                <tr>
                    <td colspan="2" align="left">
                        <span>
                        ${ _("This contribution has not been assessed yet.")}<br>
                        ${ _("You are not allowed to perform the assessment on this contribution.")}
                        </span>
                    </td>
                </tr>
            % endif
            % if len (ConfReview.getReviewingQuestions()) > 0 :
            <tr>
                <td class="dataCaptionTD" style="white-space: nowrap; width: 50px">
                    <span class="titleCellFormat">${ _("Reviewing questions:")}</span>
                </td>
                <td id="questionListDisplay">
                </td>
            </tr>
            % endif
            <tr>
                <td class="dataCaptionTD" style="white-space: nowrap; width: 50px"><span class="titleCellFormat">${ _("Comments")}:</span></td>
                <td>
                    <div id="inPlaceEditComments">${Review.getRefereeJudgement().getComments() | h, html_breaks}</div>
                </td>
            </tr>
            <tr>
                <td class="dataCaptionTD" style="white-space: nowrap; width: 50px"><span class="titleCellFormat"><strong>${ _("Assessment")}:</strong></span></td>
                <td>
                    <div id="statusDiv">
                        <div id="initialStatus" style="display:inline">${ Review.getRefereeJudgement().getJudgement() }</div>
                        <div id="inPlaceEditJudgement" style="display:inline"></div>
                    </div>
                </td>
            </tr>
            <tr><td colspan=4>

            </tr>
        % endif
        % if IsReferee:
            <tr>
                <td colspan="3" style="padding-top: 20px">
                    <span id="submitbutton" align="right"></span>
                    <span id="submitHelpPopUp" style="display:${'span' if not FinalJudge else 'none'}" align="right"></span>
                    <span id="submittedmessage"></span>
                </td>
            </tr>
        % endif
</table>
</td></tr>
% endif
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
                        current: 'refereeJudgement'
                        }, ${ ConfReview.getStatusesDictionary() }, "${FinalJudge}", observer);

    var initialValue = ${ Review.getRefereeJudgement().getComments() | n,j};
    if (initialValue == '') {
        initialValue = 'No comments';
    }

    $E('inPlaceEditComments').set(new TextAreaEditWidget('reviewing.contribution.changeComments',
            {conference: '${ Contribution.getConference().getId() }',
             contribution: '${ Contribution.getId() }',
             current: 'refereeJudgement'},initialValue).draw());


    % if len (ConfReview.getReviewingQuestions()) > 0 :
        $E("questionListDisplay").set('');
        % for q in ConfReview.getReviewingQuestions():
            var newDiv = Html.div({style:{paddingLeft:'5px', marginLeft:'10px'}});

            newDiv.append(Html.span(null,${q.getText() | n,j}));
            newDiv.append(Html.br());

            if (firstLoad) {
                % if Review.getRefereeJudgement().getAnswer(q.getId()) is None:
                    var initialValue = "${ Review.getRefereeJudgement().createAnswer(q.getId()).getRbValue() }";
                % else:
                    var initialValue = "${ Review.getRefereeJudgement().getAnswer(q.getId()).getRbValue() }";
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
                                                    current: 'refereeJudgement'
                                                    }));

            $E("questionListDisplay").append(newDiv);
            $E("questionListDisplay").append(Html.br());

        % endfor
    % endif
}

var showValues = function() {
    indicoRequest('reviewing.contribution.changeJudgement',
            {
                conference: '${ Contribution.getConference().getId() }',
                contribution: '${ Contribution.getId() }',
                current: 'refereeJudgement'
            },
            function(result, error){
                if (!error) {
                    if(!submitted){
                        $E('inPlaceEditJudgement').set(result);
                    }
                }
            }
        )

    indicoRequest('reviewing.contribution.getCriteria',
            {
                conference: '${ Contribution.getConference().getId() }',
                contribution: '${ Contribution.getId() }',
                current: 'refereeJudgement'
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


var submitted = ${jsonEncode(Review.getRefereeJudgement().isSubmitted() or not IsReferee)};

var updatePage = function (){
    if (submitted) {
        % if IsReferee:
        submitButton.set($T('Undo sending'));
        $E('submittedmessage').set($T('Assessment has been sent'));
        % endif
        if($E('initialStatus')) {
            $E('statusDiv').remove($E('initialStatus'));
        }
        showValues();
    } else {
        % if IsReferee:
        submitButton.set($T('Send'));
        % if not Review.isAuthorSubmitted() or not FinalJudge:
            submitButton.dom.disabled = true;
            var HelpImg = Html.img({src: '${ Config.getInstance().getSystemIconURL("help") }', style: {marginLeft: '5px', verticalAlign: 'middle'}});
            $E('submitHelpPopUp').append(HelpImg);
            % if not FinalJudge:
                   var submitHelpPopUpText = function(event) {
                      IndicoUI.Widgets.Generic.tooltip(this, event, "<span style='padding:3px'>You must give your assessment before sending.</span>");
                        }
            % endif
            $E('submitHelpPopUp').dom.onmouseover = submitHelpPopUpText;
        % endif
        $E('submittedmessage').set($T('Assessment not sent yet'));
        % endif
        showWidgets();
    }
}


% if IsReferee:
var submitButton = new IndicoUI.Widgets.Generic.simpleButton($E('submitbutton'), 'reviewing.contribution.setSubmitted',
        {
            conference: '${ Contribution.getConference().getId() }',
            contribution: '${ Contribution.getId() }',
            current: 'refereeJudgement',
            value: true
        },
        function(result, error){
            if (!error) {
                location.reload(true)
            } else {
                new AlertPopup($T("Error"), error.message).open();
            }
        },
        $T('Send')
);
% endif

updatePage();

</script>
% endif
