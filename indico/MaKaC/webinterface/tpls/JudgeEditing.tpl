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
        <td colspan="5" class="groupTitle" style="border: none">${ _("Give opinion on the layout of a contribution")}
            ${inlineContextHelp(_('Here is displayed the assessment given by the Layout Reviewer.<br/>Only the Layout Reviewer of this contribution can change this.'))}
        </td>
    </tr>
    <tr>
        <td colspan="5" style="padding: 1em 0;">
            <h3>Paper files</h3>
            ${ render_template('events/paper_reviewing/mako_compat/paper_file_list.html',
                               paper_files=Contribution.paper_files) }
            <h3>Questionnaire</h3>
        </td>
    </tr>
     % if len (ConfReview.getLayoutQuestions()) > 0 :
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Reviewing questions")}:</span></td>
        <td width="60%" id="criteriaListDisplay">
        </td>
    </tr>
    % endif
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Comments")}:</span></td>
        <td>
            <div id="inPlaceEditComments"></div>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"><strong>${ _("Assessment")}:</strong></span></td>
        <td>
            <div id="statusDiv">
                <div id="initialStatus" style="display:inline">${ Editing.getJudgement() }</div>
                <div id="inPlaceEditJudgement" style="display:inline"></div>
            </div>
            <div id="commentsMessage" style="padding-top:5px;">
                ${ _("The comments and your assessment, will be sent by e-mail to the author(s)")}
            </div>
        </td>
    </tr>
    % if not Editing.getJudgement():
        <% display = 'span' %>
    % else:
            <% display = 'none' %>
    % endif
    <tr>
        <td colspan="10" style="padding-top: 20px;">
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
                        {conference: '${ conf.getId() }',
                        contribution: '${ Contribution.id }',
                        current: 'editorJudgement'
                        }, ${ ConfReview.getDefaultStatusesDictionary() },
                        "${ Editing.getJudgement() }", observer);

    var initialValue = ${ Editing.getComments() | n,j };
    if (initialValue == '') {
        initialValue = 'No comments';
    }

    $E('inPlaceEditComments').set(new TextAreaEditWidget('reviewing.contribution.changeComments',
            {conference: '${ conf.getId() }',
             contribution: '${ Contribution.id }',
             current: 'editorJudgement'},initialValue).draw());


    % if len (ConfReview.getLayoutQuestions()) > 0 :
        $E("criteriaListDisplay").set('');

        % for c in ConfReview.getLayoutQuestions():

            var newDiv = Html.div({style:{borderLeft:'1px solid #777777', paddingLeft:'5px', marginLeft:'10px'}});
            newDiv.append(Html.span(null,${c.getText() | n,j}));
            newDiv.append(Html.br());

            if (firstLoad) {
                % if Editing.getAnswer(c.getId()) is None:
                    var initialValue = "${ Editing.createAnswer(c.getId()).getRbValue() }";
                % else:
                    var initialValue = "${ Editing.getAnswer(c.getId()).getRbValue() }";
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
                                                    {
                                                        conference: '${ conf.getId() }',
                                                        contribution: '${ Contribution.id }',
                                                        criterion: '${ c.getId() }',
                                                        current: 'editorJudgement'
                                                    }));

            $E("criteriaListDisplay").append(newDiv);
            $E("criteriaListDisplay").append(Html.br());

        % endfor
    % endif
}

var showValues = function() {
    indicoRequest('reviewing.contribution.changeComments',
            {
                conference: '${ conf.getId() }',
                contribution: '${ Contribution.id }',
                current: 'editorJudgement'
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
                conference: '${ conf.getId() }',
                contribution: '${ Contribution.id }',
                current: 'editorJudgement'
            },
            function(result, error){
                if (!error) {
                    $E('inPlaceEditJudgement').set(result);
                }
            }
        )

    indicoRequest('reviewing.contribution.getCriteria',
            {
                conference: '${ conf.getId() }',
                contribution: '${ Contribution.id }',
                current: 'editorJudgement'
            },
            function(result, error){
                if (!error) {
                    if (result.length > 0) {
                        $E('criteriaListDisplay').set('');
                        for (var i = 0; i<result.length; i++) {
                            $E('criteriaListDisplay').append(result[i]);
                            $E('criteriaListDisplay').append(Html.br());
                        }
                    }

                }
            }
        )
}



% if Editing.isSubmitted():
var submitted = true;
% else:
var submitted = false;

% endif

var updatePage = function (firstLoad){
    if (submitted) {
        if($E('initialStatus')) {
            $E('statusDiv').remove($E('initialStatus'));
        }
        submitButton.set('Modify assessment');
        $E('submittedmessage').set('Assessment has been submitted');
        showValues();
    } else {
        if ("${ Editing.getJudgement() }" == "None") {
            submitButton.dom.disabled = true;
        }
        submitButton.set('Submit');
        $E('submittedmessage').set('Assessment not yet submitted');
        showWidgets(firstLoad);
    }
}

var submitButton = new IndicoUI.Widgets.Generic.simpleButton($E('submitbutton'), 'reviewing.contribution.setSubmitted',
        {
            conference: '${ conf.getId() }',
            contribution: '${ Contribution.id }',
            current: 'editorJudgement',
            value: true
        },
        function(result, error){
            if (!error) {
                submitted = !submitted;
               /* updatePage(false)*/
               location.href = "";
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
