    <%= items %>

    <% if hasPaperReviewing: %>

     <table cellspacing="0" align="center" width="100%">
        <tr>
            <td colspan="3"><div class="groupTitle"><%= _("List of contribution templates")%></div></td>
        </tr>

        <%= ContributionReviewingTemplatesList %>
     </table>

    <%end%>