<%page args="Review=None, ShowReferee=None, format=None, showTitle=True"/>

<div class="historyReviewJudgment">
    <table>
        <tr>
            % if showTitle:
            <td class="dataCaptionTD" style="white-space: nowrap; width: 50px">
                <span class="titleCellFormat" style="font-size: 12px; font-weight: bold">${ _("Referee:")}</span>
            </td>
            % endif
            <td>
                <div class="contributionReviewingStatus ${getStatusClass(Review.getJudgement())}" style="margin-top: 0">
                    ${getStatusText(Review.getJudgement())}
                </div>
                <div>
                ${ _("submitted on") } <span style="font-style: italic">${ Review.getAdjustedSubmissionDate().strftime(format) }</span>
                    % if ShowReferee:
                       ${ _("by") } <span style="font-style: italic">${ Review.getAuthor().getStraightFullName()}</span>
                    % endif
                </div>
                % if Review.getComments():
                    <div class="historyReviewJugmentComments">
                        <span style= "font-weight: bold">${_("Comments")}</span><br/>
                        ${ Review.getComments() | h, html_breaks}
                    </div>
                % endif
                % if Review.getAnswers():
                    <div class="historyReviewJugmentComments">
                        <span style= "font-weight: bold">${_("Answers")}</span>
                        % for a in Review.getAnswers():
                            <br/>${ a }
                        % endfor
                    </div>
                % endif
            </td>
       </tr>
    </table>
</div>