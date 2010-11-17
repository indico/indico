<form action="<%= postURL %>" method="POST">
    <table align="center" width="50%" border="0" style="border-left: 1px solid #777777">
		<tr>
			<td class="groupTitle" colspan="2"> <%= _("Propose to be accepted")%></td>
        </tr>
        <tr>
            <td bgcolor="white" colspan="2">
                <font color="#5294CC"> <%= _("Abstract title")%>:</font><font color="gray"> <%= abstractTitle %><br></font>
                <font color="#5294CC"> <%= _("Track")%>:</font><font color="gray"> <%= trackTitle %></font>
				<br>
				<span style="border-bottom: 1px solid #5294CC; width: 100%">&nbsp;</span>
			</td>
		</tr>
		<%= contribTypes %>
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
			<td nowrap colspan="2"><span class="titleCellFormat"> <%= _("Please enter below a comment which justifies your request")%>:</span>
                <table>
                    <tr>
                        <td>
                            <textarea cols="50" rows="5" name="comment"></textarea>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
		<tr><td  colspan="2">&nbsp;</td></tr>
        <tr>
            <td class="buttonsSeparator" colspan="2" align="center" style="padding:10px">
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
