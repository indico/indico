<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

% if User is not None:
    <% contributions = Conference.getContribsForSubmitter(User) %>
    % if len(contributions) > 0:
        <table class="groupTable" align="center" cellspacing="0"  width="100%">
        <tr>
        <td style="padding-top:10px; padding-left:5px;">
            <table class="infoTable" cellspacing="0" width="100%">
                <tr>
                    <td nowrap class="tableHeader">${ _("Id") }</td>
                    <td nowrap class="tableHeader">${ _("Contribution") }</td>
                    % if Conference.getConfPaperReview().hasReviewing():
                    <td nowrap class="tableHeader">${ _("Reviewing Status") }</td>
                    % endif
                    <td nowrap class="tableHeader" style="text-align:right;">${ _("Actions") }</td>
                    </tr>
                % for c in contributions:
                <tr class="infoTR">
                    <td class="content" valign="top">
                        ${str(c.getId())}
                    </td>
                    <td class="content" valign="top">
                        ${c.getTitle()}
                    </td>
                    % if Conference.getConfPaperReview().hasReviewing():
                    <td class="content" valign="top">
                        ${"<br>".join(c.getReviewManager().getLastReview().getReviewingStatus(forAuthor = True))}
                    </td>
                    % endif
                    <td nowrap class="content" valign="top" style="text-align: right;">
                    % if c.canModify(self_._aw):
                            <a href="${urlHandlers.UHContributionModification.getURL(c)}">${ _("Edit") }</a><span class="horizontalSeparator">|</span><a href="${urlHandlers.UHContributionDisplay.getURL(c)}">View</a>
                    % else:
                            <a href="${urlHandlers.UHContributionDisplay.getURL(c)}">${ _("View") }</a>
                    % endif
                    </td>
                </tr>
                % endfor
            </table>
            </td>
            </tr>
            </table>
    % endif
% endif
