<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.timezoneUtils import nowutc %>
<% from MaKaC.conference import ContribStatusNone %>

<% dueDateFormat = "%a %d %b %Y" %>

<% if ConfReview.getEditedContributions(User): %>
<table class="Revtab" width="90%%" cellspacing="0" align="center" border="0" style="padding-left:2px; padding-top: 10px">
    <tr>
        <td nowrap class="groupTitle" colspan=4><%= _("Judge editing of the contribution")%></td>
    </tr>
    <tr>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;"><%= _("Id")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;"><%= _("Title")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;"><%= _("State")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;"><%= _("Deadline")%></td>
    </tr>
   
    <% for c in ConfReview.getEditedContributions(User): %>
        <% if not isinstance(c.getStatus(), ContribStatusNone): %>
        <tr valign="top" onmouseover="this.style.backgroundColor='#ECECEC'" onmouseout="this.style.backgroundColor='transparent'">
            <td style="padding-right:5px;padding-left:5px;"><%= c.getId() %></td>
            <td style="padding-right:5px;padding-left:5px;"><a href="<%= urlHandlers.UHContributionEditingJudgement.getURL(c) %>"><%= c.getTitle() %></a></td>
            <td style="padding-right:5px;padding-left:5px;">
                <% if c.getReviewManager().getLastReview().getEditorJudgement().isSubmitted(): %>
                    <span><%= _("Layout judgement given")%></span>
                <% end %>
                <% else: %>
                    <span><%= _("Layout judgement not given yet")%></span>
                    <% if c.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted(): %>
                    <span><br><%= _("but Referee already judged contribution")%></span>
                    <% end %>
                <% end %>
            </td>   
            <td style="padding-right:5px;padding-left:5px;">
            <% date = c.getReviewManager().getLastReview().getAdjustedEditorDueDate() %>
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
<% if not ConfReview.getEditedContributions(User):%>
<p style="padding-left: 25px;"><font color="gray"><%= _("There are no contributions assigned to you to judge yet.")%></font></p>