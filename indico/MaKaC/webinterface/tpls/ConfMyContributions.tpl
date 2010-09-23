<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

<% if User is not None: %>
    <% contributions = Conference.getContribsForSubmitter(User) %>
    <% if len(contributions) > 0: %>
        <table class="groupTable" width="70%%" align="center" cellspacing="0">
        <tr>
            <td class="groupTitle" colspan="4" style="padding-top:25px;">Contributions</td>
        </tr>
        <tr>
        <td style="padding-top:10px;">
            <table class="infoTable" cellspacing="6">
                <tr>
                    <td nowrap class="data">
                        <b>Id</b>
                    </td>
                    <td nowrap class="data">
                        <b>Name</b>
                    </td>
                    <% if Conference.hasEnabledSection("paperReviewing"): %>
                    <td nowrap class="data">
                        <b>Reviewing Status</b>
                    </td>
                    <% end %>
                    </tr>
                <% for c in contributions: %>
                <tr>
                    <td class="content" valign="top">
                        <%=str(c.getId())%>
                    </td>
                    <td class="content" valign="top">
                        <a href="<%=urlHandlers.UHContributionDisplay.getURL(c)%>"><%=c.getTitle()%></a>
                    </td>
                    <% if Conference.hasEnabledSection("paperReviewing"): %>
                    <td class="content" valign="top">
                        <%="<br>".join(c.getReviewManager().getLastReview().getReviewingStatus())%>
                    </td>
                    <% end %>
                </tr>
                <% end %>
            </table>
            </td>
            </tr>
            </table>
    <% end %>
<% end %>