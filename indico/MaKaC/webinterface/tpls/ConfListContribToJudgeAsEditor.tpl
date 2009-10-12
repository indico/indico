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
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"><%= _("Id")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"><%= _("Title")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"><%= _("State")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"><%= _("Deadline")%></td>
    </tr>
   
    <% for c in ConfReview.getEditedContributions(User): %>
        <% if not isinstance(c.getStatus(), ContribStatusNone): %>
        <tr valign="top">
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;"><%= c.getId() %></td>
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;"><a href="<%= urlHandlers.UHContributionEditingJudgement.getURL(c) %>"><%= c.getTitle() %></a></td>
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <% if c.getReviewManager().getLastReview().getEditorJudgement().isSubmitted(): %>
                    <span style="color:green;"><%= _("Layout judgement given")%></span>
                <% end %>
                <% else: %>
                    <span style="color:red;"><%= _("Layout judgement not given yet")%></span>
                    <% if c.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted(): %>
                    <span style="color:green;"><br><%= _("but Referee already judged contribution")%></span>
                    <% end %>
                <% end %>
            </td>   
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
            <% date = c.getReviewManager().getLastReview().getAdjustedEditorDueDate() %>
            <% if date is None: %>
                <%= _("Deadline not set.")%>
            <% end %>
            <% else: %>
                <% if date < nowutc() and not c.getReviewManager().getLastReview().getEditorJudgement().isSubmitted(): %>
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
<% if not ConfReview.getEditedContributions(User):%>
<p style="padding-left: 25px;"><font color="gray"><%= _("There are no contributions assigned to you to judge yet.")%></font></p>