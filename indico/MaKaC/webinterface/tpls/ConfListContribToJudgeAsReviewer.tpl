<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.timezoneUtils import nowutc %>
<% from MaKaC.conference import ContribStatusNone %>

<% dueDateFormat = "%a %d %b %Y" %>

<% if ConfReview.getReviewedContributions(User): %>

<table class="Revtab" width="90%%" cellspacing="0" align="center" border="0" style="padding-left:2px; padding-top: 10px">
    <tr>
        <td nowrap class="groupTitle" colspan=4><%= _("Give advice on content of the contribution")%></td>
    </tr>
    <tr>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;"><%= _("Id")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;"><%= _("Title")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;"><%= _("State")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;"><%= _("Deadline")%></td>
    </tr>
   
    <% for c in ConfReview.getReviewedContributions(User): %>
        <% if not isinstance(c.getStatus(), ContribStatusNone): %>
        <tr valign="top" onmouseover="this.style.backgroundColor='#ECECEC'" onmouseout="this.style.backgroundColor='transparent'">
            <td style="padding-right:5px;padding-left:5px;"><%= c.getId() %></td>
            <td style="padding-right:5px;padding-left:5px;"><a href="<%= urlHandlers.UHContributionGiveAdvice.getURL(c) %>"><%= c.getTitle() %></a></td>
            <td style="padding-right:5px;padding-left:5px;">
                <% if c.getReviewManager().getLastReview().hasGivenAdvice(User): %>
                    <span style="color:green;"><%= _("Advice given")%></span>
                <% end %>
                <% else: %>
                    <span style="color:red;"><%= _("Advice not given yet")%></span>
                    <% if c.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted(): %>
                    <span style="color:green;"><br><%= _("but Referee already judged contribution")%></span>
                    <% end %>
                <% end %>
            </td>
            <td style="padding-right:5px;padding-left:5px;">
            <% date = c.getReviewManager().getLastReview().getAdjustedReviewerDueDate() %>
            <% if date is None: %>
                <%= _("Deadline not set.")%>
            <% end %>
            <% else: %>
                <% if date < nowutc() and not c.getReviewManager().getLastReview().hasGivenAdvice(User): %>
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
<% end %>
<% if not ConfReview.getReviewedContributions(User):%>
<p style="padding-left: 25px;"><font color="gray"><%= _("There are no contributions assigned to you to judge yet.")%></font></p>