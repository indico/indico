<% declareTemplate(newTemplateStyle=True) %>
<% format = "%a %d %b %Y at %H\x3a%M" %>

<!-- Final reviewing of the referee -->
<% if ConferenceChoice == 2 or ConferenceChoice == 4: %>
    <% if Review.getRefereeJudgement().isSubmitted(): %>
<table class="newsDisplayItem" width="90%%" align="left" border="0">
    <tr>
        <td>
            <% includeTpl ('FinalJudgementDisplay', Review = Review, ShowReferee = ShowReviewingTeam) %>
        </td>
    </tr>
</table>
    <% end %>
<% end %>
<!-- Judgement of the editor -->

<% if Editing.isSubmitted() and not (ConferenceChoice == 2 or ConferenceChoice == 1): %>
<table class="newsDisplayItem" width="90%%" align="left" border="0">
    <tr>
        <td>
            <% includeTpl ('EditingJudgementDisplay', Editing = Editing, ShowEditor = ShowReviewingTeam) %>
        </td>
    </tr>
</table>
<% end %>

<!-- List of advices from the reviewers -->
<% if Review.anyReviewerHasGivenAdvice() and not (ConferenceChoice == 3 or ConferenceChoice == 1): %>
<table width="90%%" align="left" border="0">
    <tr>
        <td>
            <table class="newsDisplayItem" cellspacing="0" cellpadding="2" width="100%%">
            <% for advice in AdviceList: %>
                <% if advice.isSubmitted(): %>
                    <% includeTpl ('AdviceJudgementDisplay', advice = advice, ShowReviewer = ShowReviewingTeam) %>
                <% end %>
            <% end %>
            </table>
        </td>
    </tr>
</table>
<% end %>
