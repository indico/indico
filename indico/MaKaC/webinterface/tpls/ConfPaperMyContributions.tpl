<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

<% if User is not None: %>
    <% contributions = Conference.getContribsForSubmitter(User) %>
    <% if len(contributions) > 0: %>
        <table class="groupTable" align="center" cellspacing="0"  width="100%%">
        <tr>
            <td class="groupTitle" colspan="4" style="padding-top:25px;">Contributions</td>
        </tr>
        <tr>
        <td style="padding-top:10px; padding-left:5px;">
            <table class="infoTable" cellspacing="0" width="100%%">
                <tr>
                    <td nowrap class="data">
                        <b>Id</b>
                    </td>
                    <td nowrap class="data">
                        <b>Name</b>
                    </td>
                    <% if Conference.getConfPaperReview().hasReviewing(): %>
                    <td nowrap class="data">
                        <b>Reviewing Status</b>
                    </td>
                    <% end %>
                    <td nowrap class="data">

                    </td>
                    </tr>
                <% for c in contributions: %>
                <tr class="infoTR">
                    <td class="content" valign="top">
                        <%=str(c.getId())%>
                    </td>
                    <td class="content" valign="top">
                        <%=c.getTitle()%>
                    </td>
                    <% if Conference.getConfPaperReview().hasReviewing(): %>
                    <td class="content" valign="top">
                        <%="<br>".join(c.getReviewManager().getLastReview().getReviewingStatus(forAuthor = True))%>
                    </td>
                    <% end %>
                    <td nowrap class="content" valign="top" style="text-align: right;">
                    <% if c.canModify(self._aw): %>
                            <a href="<%=urlHandlers.UHContributionModification.getURL(c)%>">Edit</a><span class="horizontalSeparator">|</span><a href="<%=urlHandlers.UHContributionDisplay.getURL(c)%>">View</a>
                    <% end %>
                    <% else: %>
                        <% url = urlHandlers.UHContributionDisplay.getURL(c) %>
                        <% url.addParam("s",1) %>
                            <a href="<%=url%>">Upload Paper</a>
                    <% end %>
                    </td>
                </tr>
                <% end %>
            </table>
            </td>
            </tr>
            </table>
    <% end %>
<% end %>