<%page args="Editing=None, AdviceList=None, Review=None, ConferenceChoice=None"/>
<% format = "%a %d %b %Y at %H\x3a%M" %>

<!-- Final reviewing of the referee -->
% if ConferenceChoice == 2 or ConferenceChoice == 4:
    % if Review.getRefereeJudgement().isSubmitted():
            <%include file="FinalJudgementDisplay.tpl" args="Review = Review.getRefereeJudgement(), ShowReferee = ShowReviewingTeam, format=format"/>
    % endif
% endif
<!-- Judgement of the editor -->

% if Editing.isSubmitted() and not (ConferenceChoice == 2 or ConferenceChoice == 1):
    <%include file="EditingJudgementDisplay.tpl" args="Editing = Editing, ShowEditor = ShowReviewingTeam, format=format"/>
% endif

<!-- List of advices from the reviewers -->
% if Review.anyReviewerHasGivenAdvice() and not (ConferenceChoice == 3 or ConferenceChoice == 1):
            % for advice in AdviceList:
                % if advice.isSubmitted():
                    <%include file="AdviceJudgementDisplay.tpl" args="Advice = advice, ShowReviewer = ShowReviewingTeam, format=format"/>
                % endif
            % endfor
% endif
