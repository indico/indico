<%page args="Editing=None, ShowEditor=None, format=None, showTitle=True"/>

<div class="historyReviewJudgment">
    <table>
        <tr>
            % if showTitle:
            <td class="dataCaptionTD" style="white-space: nowrap; width: 50px">
                <span class="titleCellFormat" style="font-size: 12px;">${ _("Layout:")}</span>
            </td>
            % endif
            <td>
                <div class="contributionReviewingStatus ${getStatusClass(Editing.getJudgement())}" style="margin-top: 0">
                    ${getStatusText(Editing.getJudgement())}
                </div>
                <div>
                ${ _("submitted on") } <span style="font-style: italic">${ Editing.getAdjustedSubmissionDate().strftime(format) }</span>
                    % if ShowEditor:
                       ${ _("by") } <span style="font-style: italic">${ Editing.getAuthor().getStraightFullName()}</span>
                    % endif
                </div>
                % if Editing.getComments():
                    <div class="historyReviewJugmentComments"">
                        <span style= "font-weight: bold">${_("Comments")}</span><br/>
                        ${ Editing.getComments() | h, html_breaks}
                    </div>
                % endif
                % if Editing.getAnswers():
                    <div class="historyReviewJugmentComments">
                        <span style= "font-weight: bold">${_("Answers")}</span>
                        % for a in Editing.getAnswers():
                            <br/>${ a }
                        % endfor
                    </div>
                % endif
            </td>
       </tr>
    </table>
</div>