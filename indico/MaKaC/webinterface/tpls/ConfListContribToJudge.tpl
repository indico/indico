<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.timezoneUtils import nowutc %>
<% from MaKaC.conference import ContribStatusNone %>

<% dueDateFormat = "%a %d %b %Y" %>

<% if ConfReview.getJudgedContributions(User): %>
<table class="Revtab" width="90%%" cellspacing="0" align="center" border="0" style="padding-left:2px; padding-top: 10px">
    <tr>
        <td nowrap class="groupTitle" colspan=4><%= _("Contributions to judge as Referee")%></td>
    </tr>
    <tr>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"><%= _("Id")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"><%= _("Title")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"><%= _("State")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"><%= _("Deadline")%></td>
    </tr>
   
    <% for c in ConfReview.getJudgedContributions(User): %>
        <% if not isinstance(c.getStatus(), ContribStatusNone): %>
	    <tr valign="top">
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;"><%= c.getId() %></td>
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;"><a href="<%= urlHandlers.UHContributionModifReviewing.getURL(c) %>"><%= c.getTitle() %></a></td>
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
            <% if c.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted(): %>
                <span style="color:green;"><%= _("Judged:")%> <%= c.getReviewManager().getLastReview().getRefereeJudgement().getJudgement() %></span>
            <% end %>
            <% else: %>
                <span style="color:red;"><%= _("Not judged yet")%></span><br>
                <%= "<br>".join(c.getReviewManager().getLastReview().getReviewingStatus()) %>
            <% end %>
            </td>    
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <% date = c.getReviewManager().getLastReview().getAdjustedRefereeDueDate() %>
                <% if date is None: %>
                    <%= _("Deadline not set.")%>
                <% end %>
                <% else: %>
                <% if date < nowutc() and not c.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted(): %>
                    <span style="color:red;">
                    <% end %>
                    <% else: %>
                    <span style="color:green;">
                    <% end %>
                    <%= date.strftime(dueDateFormat) %>
                    </span>
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