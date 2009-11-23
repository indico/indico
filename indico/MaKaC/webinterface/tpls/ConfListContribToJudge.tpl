<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.timezoneUtils import nowutc %>
<% from MaKaC.conference import ContribStatusNone %>

<% dueDateFormat = "%a %d %b %Y" %>

<% if ConfReview.getJudgedContributions(User): %>
<table class="Revtab" width="90%%" cellspacing="0" align="center" border="0" style="padding-left:2px; padding-top: 10px">
    <tr>
        <td nowrap class="groupTitle" colspan=4 style=""><%= _("Contributions to judge as Referee")%></td>
    </tr>
    <tr>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;"><%= _("Id")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;"><%= _("Title")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;"><%= _("State")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;"><%= _("Deadline")%></td>
    </tr>
   
    <% for c in ConfReview.getJudgedContributions(User): %>
        <% if not isinstance(c.getStatus(), ContribStatusNone): %>
	    <tr valign="top" onmouseover="this.style.backgroundColor='#ECECEC'" onmouseout="this.style.backgroundColor='transparent'">
            <td style="padding-right:5px;padding-left:5px;"><%= c.getId() %></td>
            <td style="padding-right:5px;padding-left:5px;"><a href="<%= urlHandlers.UHContributionModifReviewing.getURL(c) %>"><%= c.getTitle() %></a></td>
            <td style="padding-right:5px;padding-left:5px;">
            <% if c.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted(): %>
                <span><%= _("Judged:")%></span> <%= c.getReviewManager().getLastReview().getRefereeJudgement().getJudgement() %>
            <% end %>
            <% else: %>
                <span><%= _("Not judged yet")%></span><br>
                <%= "<br>".join(c.getReviewManager().getLastReview().getReviewingStatus()) %>
            <% end %>
            </td>    
            <td style="padding-right:5px;padding-left:5px;" onmouseover="this.style.borderColor='#ECECEC'" onmouseout="this.style.borderColor='transparent'">
                <% date = c.getReviewManager().getLastReview().getAdjustedRefereeDueDate() %>
                <% if date is None: %>
                    <%= _("Deadline not set.")%>
                <% end %>
                <% else: %>
                    <span><%= date.strftime(dueDateFormat) %></span>
                <% end %>
            </td>                    
        </tr>
        <% end %>
    <% end %>
</table>
<br>
<% end %>
<% if not ConfReview.getJudgedContributions(User):%>
<p style="padding-left: 25px;"><font color="gray"><%= _("There are no contributions assigned to you to judge yet.")%></font></p>