<form action=<%= postURL %> method="POST">
    <table width="60%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> <%= _("Propose to be rejected")%></td>
        </tr>
        <% if len(tracks) > 0: %>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> <%= _("Proposed track")%></span>
            </td>
            <td><select name="track"><%= tracks %></select></td>
        </tr>
        <% end %>
        <% else: %>
        <tr>
            <td colspan="2">
                <span class="titleCellFormat"> <b><%= _("This abstract has not been included in any track, if you want to include it now click")%> <a href=<%= changeTrackURL %>><%= _("here")%></a></b> </span>
            </td>
        </tr>
        <% end %>
        <tr>
            <td colspan="5" class="groupTitle" style="border: none"><%= _("Questions for abstract review")%>
                <% inlineContextHelp(_('Here is displayed the judgement given by the Abstract Reviewers.')) %>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Reviewing questions")%></span></td>
            <td width="60%%" id="questionListDisplay">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> <%= _("Comment")%></span>
            </td>
            <td>
                <textarea cols="60" rows="5" name="comment"><%= comment %></textarea>
            </td>
        </tr>
        <tr>
            <td colspan="2">&nbsp;</td>
        </tr>
        <tr>
            <td colspan="2">
                <input type="submit" class="btn" name="OK" value="<%= _("submit")%>">
                <input type="submit" class="btn" name="CANCEL" value="<%= _("cancel")%>">
            </td>
        </tr>
    </table>
</form>
<script type="text/javascript">

var showQuestions = function() {

    <% if len (abstractReview.getReviewingQuestions()) == 0 : %>
        $E('questionListDisplay').set("No reviewing questions proposed for the abstract review.");
    <% end %>
    <% else: %>
        $E("questionListDisplay").set('');
        <% for q in abstractReview.getReviewingQuestions(): %>
            var newDiv = Html.div({style:{borderLeft:'1px solid #777777', paddingLeft:'5px', marginLeft:'10px'}});

            newDiv.append(Html.span(null,"<%=q%>"));
            newDiv.append(Html.br());

            newDiv.append(new IndicoUI.Widgets.Generic.radioButtonSimpleField(
                                                    null,
                                                    'horizontal2',
                                                    <%= str(range(len(abstractReview.reviewingQuestionsAnswers))) %>,
                                                    <%= str(abstractReview.reviewingQuestionsLabels) %>,
                                                    <%= str(abstractReview.initialSelectedAnswer) %>));

            $E("questionListDisplay").append(newDiv);
            $E("questionListDisplay").append(Html.br());

        <% end %>
    <% end %>
}

showQuestions();

</script>
