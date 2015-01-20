<%page args="Advice=None, ShowReviewer=None, format=None, showTitle=True"/>

<div class="historyReviewJudgment">
    <table>
        <tr>
            % if showTitle:
            <td class="dataCaptionTD" style="white-space: nowrap; width: 50px">
                <span class="titleCellFormat" style="font-size: 12px;">${ _("Content:")}</span>
            </td>
            % endif
            <td>
                <div class="contributionReviewingStatus ${getStatusClass(Advice.getJudgement())}" style="margin-top: 0;">
                    ${getStatusText(Advice.getJudgement())}
                </div>
                <div>
                ${ _("submitted on") } <span style="font-style: italic">${ Advice.getAdjustedSubmissionDate().strftime(format) }</span>
                    % if ShowReviewer:
                       ${ _("by") } <span style="font-style: italic">${ Advice.getAuthor().getStraightFullName()}</span>
                    % endif
                </div>
                % if Advice.getComments():
                    <div  class="historyReviewJugmentComments">
                        <span style= "font-weight: bold">${_("Comments")}</span><br/>
                        ${ Advice.getComments() | h, html_breaks}
                    </div>
                % endif
                % if Advice.getAnswers():
                    <div  class="historyReviewJugmentComments">
                        <span style= "font-weight: bold">${_("Criteria Evaluation")}</span>
                        % for a in Advice.getAnswers():
                            <br/>${ a }
                        % endfor
                    </div>
                % endif
            </td>
       </tr>
    </table>
</div>
