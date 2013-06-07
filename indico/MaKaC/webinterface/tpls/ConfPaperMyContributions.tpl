<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

% if User is not None:
    <% contributions = Conference.getContribsForSubmitter(User) %>
    % if len(contributions) > 0:
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
                        <a href="${urlHandlers.UHContributionModification.getURL(c)}">${ _("Edit") }</a><span class="horizontalSeparator">|</span><a href="${urlHandlers.UHContributionDisplay.getURL(c)}">${ _("View") }</a>
                % else:
                    <% url = urlHandlers.UHContributionDisplay.getURL(c) %>
                    <% url.addParam("s",1) %>
                        <a href="${url}">${ _("Upload Paper") }</a>
                % endif
                </td>
            </tr>
            % endfor
        </table>
    % endif
% endif
