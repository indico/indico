<table width="90%%" align="center" border="0">
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">
            <%= _("Abstract Reviewer default due date")%>
        </span></td>
        <td class="blacktext">
            <span id="inPlaceEditDefaultAbstractReviewerDueDate">
                <% date = ConfReview.getAdjustedDefaultAbstractReviewerDueDate() %>
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


<script type="text/javascript">
new IndicoUI.Widgets.Generic.dateEditor($E('inPlaceEditDefaultAbstractReviewerDueDate'),
                   'reviewing.conference.changeAbstractReviewerDefaultDueDate',
                   {conference: '<%= ConfReview.getConference().getId() %>',
                    dueDateToChange: '<%= _("Abstract Reviewer")%>'},
                   null, true);
</script>