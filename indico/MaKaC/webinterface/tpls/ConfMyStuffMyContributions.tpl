<% declareTemplate(newTemplateStyle=True) %>
<div class="groupTitle"><%= _("My Conference Features")%></div>
<table width='100%'>
    <tr>
        <td style="padding-bottom: 50px;">
            <table>
                <%= items %>
            </table>
        </td>
    </tr>
    <% if hasPaperReviewing: %>
    <tr>
        <td>
            <table cellspacing="0" align="center" width="70%">
                <tr>
                    <td colspan="3"><div class="groupTitle">List of contributions templates</div></td>
                </tr>
                <%= ContributionReviewingTemplatesList %>
            </table>
        </td>
    </tr>
    <%end%>
</table>