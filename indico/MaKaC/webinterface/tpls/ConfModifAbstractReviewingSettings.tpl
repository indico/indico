<table width="90%%" border="0" style="padding-bottom: 10px;">
    <tr>
        <td id="reviewingModeHelp" colspan="5" class="groupTitle" style="padding-bottom: 10px; padding-left: 20px;">
            <%= _("Default date for abstract reviewing")%>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD" style="padding-left: 30px; padding-top: 15px;"><span class="titleCellFormat">
            <%= _("Abstract Reviewer Deadline")%>
        </span></td>
        <td class="blacktext" style="padding-top: 15px;">
            <span id="inPlaceEditDefaultAbstractReviewerDueDate">
                <% date = abstractReview.getAdjustedDefaultAbstractReviewerDueDate() %>
                <% if date is None: %>
                    <%= _("Date has not been set yet.")%>
                <% end %>
                <% else: %>
                    <%= formatDateTime(date) %>
                <% end %>
            </span>
        </td>
    </tr>
</table>

<table id="reviewingQuestionsTable" width="90%%" border="0" style="padding-bottom: 10px;">
    <tr>
        <td id="reviewingQuestionsHelp" colspan="5" class="groupTitle" style="padding-bottom: 10px; padding-left: 20px;"><%= _("Add questions for abstract reviewing")%></td>
    </tr>
    <tr>
        <td>
            <div id="inPlaceEditQuestions"  style="padding-top: 5px;"><%= ', '.join(abstractReview.getReviewingQuestions())%></div>
        </td>
    </tr>
</table>



<script type="text/javascript">
new IndicoUI.Widgets.Generic.dateEditor($E('inPlaceEditDefaultAbstractReviewerDueDate'),
                   'reviewing.conference.changeAbstractReviewerDefaultDueDate',
                   {conference: '<%= abstractReview.getConference().getId() %>',
                    dueDateToChange: '<%= _("Abstract Reviewer")%>'},
                   null, true);


var showReviewingQuestions = function() {
    new IndicoUI.Widgets.Generic.keywordField(
        $E('inPlaceEditQuestions'),
        'multipleLinesListItem',
        'reviewing.conference.changeAbstractQuestions',
        {conference: '<%= abstractReview.getConference().getId() %>'},
        $T('Remove this question from the list')
    );
}

showReviewingQuestions();

</script>