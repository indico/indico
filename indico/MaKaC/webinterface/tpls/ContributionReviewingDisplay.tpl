<%page args="Editing=None, AdviceList=None, Review=None, ConferenceChoice=None"/>
<% format = "%a %d %b %Y at %H\x3a%M" %>

<!-- Final reviewing of the referee -->
% if ConferenceChoice == 2 or ConferenceChoice == 4:
    % if Review.getRefereeJudgement().isSubmitted():
<table class="newsDisplayItem" width="95%" align="left" border="0">
    <tr>
        <td>
            <%include file="FinalJudgementDisplay.tpl" args="Review = Review, ShowReferee = ShowReviewingTeam, format=format"/>
        </td>
    </tr>
</table>
    % endif
% endif
<!-- Judgement of the editor -->

% if Editing.isSubmitted() and not (ConferenceChoice == 2 or ConferenceChoice == 1):
<table class="newsDisplayItem" width="95%" align="left" border="0">
    <tr>
        <td>
            <%include file="EditingJudgementDisplay.tpl" args="Editing = Editing, ShowEditor = ShowReviewingTeam, format=format"/>
        </td>
    </tr>
</table>
% endif

<!-- List of advices from the reviewers -->
% if Review.anyReviewerHasGivenAdvice() and not (ConferenceChoice == 3 or ConferenceChoice == 1):
<table width="95%" align="left" border="0">
    <tr>
        <td>
            <table class="newsDisplayItem" cellspacing="0" cellpadding="2" width="100%">
            % for advice in AdviceList:
                % if advice.isSubmitted():
                    <%include file="AdviceJudgementDisplay.tpl" args="advice = advice, ShowReviewer = ShowReviewingTeam, format=format"/>
                % endif
            % endfor
            </table>
        </td>
    </tr>
</table>
% endif