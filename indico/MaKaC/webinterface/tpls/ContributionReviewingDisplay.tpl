<% declareTemplate(newTemplateStyle=True) %>
<% format = "%a %d %b %Y at %H\x3a%M" %>

<!-- Judgement of the editor -->

<% if Editing.isSubmitted(): %>
<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td colspan="5" class="groupTitle">Editing judgement</td>
    </tr>

    <tr>
        <td>
            <% includeTpl ('EditingJudgementDisplay', Editing = Editing, ShowEditor = ShowReviewingTeam) %>
        </td>
    </tr>
</table>
<% end %>

<!-- List of advices from the reviewers -->
<% if Review.anyReviewerHasGivenAdvice(): %>
<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td colspan="5" class="groupTitle">Reviewing judgement</td>
    </tr>
    <tr>
        <td>
            <table cellspacing="0" cellpadding="5" width="100%%">
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

<!-- Final reviewing of the referee -->
<% if ConferenceChoice == 2 or ConferenceChoice == 4: %>
    <% if Review.getRefereeJudgement().getJudgement() != None: %>
<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td colspan="5" class="groupTitle">Final Reviewing</td>
    </tr>
    <tr>
        <td>
            <% includeTpl ('FinalJudgementDisplay', Review = Review, ShowReferee = ShowReviewingTeam) %>
        </td>
    </tr>
</table>
    <% end %>
<% end %>