<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

<% if User is not None: %>
    <% contributions = Conference.getContribsForSubmitter(User) %>
    <% if len(contributions) > 0: %>
        <table style="border-left:1px solid #777777;border-top:1px solid #777777;" width="70%%" align="center" cellspacing="0">
        <tr>
            <td class="groupTitle" colspan="4" style="background:#E5E5E5; color:gray; border-top:2px solid #FFFFFF; border-left:2px solid #FFFFFF">&nbsp;&nbsp;&nbsp;Contributions</td>
        </tr>
        <tr>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> 
                Id
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> 
                Name
            </td>
            <% if Conference.hasEnabledSection("paperReviewing"): %>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> 
                Reviewing Status
            </td>
            <% end %>
        </tr>
        <% for c in contributions: %>
        <tr>
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;" valign="top">
                <%=str(c.getId())%>
            </td>
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;" valign="top">
                <a href="<%=urlHandlers.UHContributionDisplay.getURL(c)%>"><%=c.getTitle()%></a>
            </td>
            <% if Conference.hasEnabledSection("paperReviewing"): %>
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;" valign="top">
                <%="<br>".join(c.getReviewManager().getLastReview().getReviewingStatus())%>
            </td>
            <% end %>
        </tr>
        <tr><td></td></tr>
        <% end %>
        </table>
    <% end %>
<% end %>