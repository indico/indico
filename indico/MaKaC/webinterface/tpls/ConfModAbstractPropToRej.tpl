<form action=<%= postURL %> method="POST">
    <table width="60%" align="left" border="0" cellspacing="6" cellpadding="2" style="padding-top:15px; padding-left:15px;">
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
            <td colspan="2" style="text-align: center;">
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
            var newDiv = Html.div({style:{marginLeft:'10px'}});

            newDiv.append(Html.span(null,"<%=q.getText()%>"));
            newDiv.append(Html.br());

            newDiv.append(new IndicoUI.Widgets.Generic.radioButtonSimpleField(
                                                    null,
                                                    <%= str(range(abstractReview.getNumberOfAnswers())) %>,
                                                    <%= str(abstractReview.getRadioButtonsLabels()) %>));

            $E("questionListDisplay").append(newDiv);
            $E("questionListDisplay").append(Html.br());

        <% end %>
    <% end %>

    var numQuestions = <%= len(abstractReview.getReviewingQuestions()) %>;
    var numAnswers = <%= abstractReview.getNumberOfAnswers() %>;
    var rbValues = <%= str(abstractReview.getRadioButtonsTitles()) %>;
    var groupName = "_GID" // The common name for all the radio buttons

    for (var i=1; i<numQuestions+1; i++) {
        for (var j=0; j<numAnswers; j++) {
            $E(groupName+i + "_" + j).dom.onmouseover = function(event) {
                var value = rbValues[this.defaultValue];
                IndicoUI.Widgets.Generic.tooltip(this, event, "<span style='padding:3px'>"+value+"</span>");
            };
        }
    }

}

showQuestions();

</script>
