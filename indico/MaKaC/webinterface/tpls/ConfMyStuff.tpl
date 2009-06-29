<% declareTemplate(newTemplateStyle=True) %>
<table width='100%'>
	<tr>
        <td>
            <table>
                <%= items %>
            </table>
        </td>
    </tr>
    <% if hasPaperReviewing: %>
    <tr>
        <td>
            <table cellspacing="0">
                <tr>
                    <td colspan="3"><div class="groupTitle">List of contributions templates</div></td>
                </tr>
                <%= ContributionReviewingTemplatesList %>
            </table>
        </td>
    </tr>
    <% end %>
</table>