<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

% if User is not None:
    <% contributions = Conference.getContribsForSubmitter(User) %>
    % if len(contributions) > 0:
        <table class="groupTable" align="center" cellspacing="0"  width="100%">
        <tr>
            <td class="groupTitle" colspan="4" style="padding-top:25px;">${ _("Contributions") }</td>
        </tr>
        <tr>
        <td style="padding-top:10px; padding-left:5px;">
            <table class="infoTable" cellspacing="0" width="100%">
                <tr>
                    <td nowrap class="data">
                        <span style="font-weight:bold;">${ _("Id") }</span>
                    </td>
                    <td nowrap class="data">
                        <span style="font-weight:bold;">${ _("Name") }</span>
                    </td>
                    % if Conference.getConfPaperReview().hasReviewing():
                    <td nowrap class="data">
                        <span style="font-weight:bold;">${ _("Reviewing Status") }</span>
                    </td>
                    % endif
                    <td nowrap class="data" style="text-align:right;">
                        <span style="font-weight:bold;">${ _("Actions") }</span>
                    </td>
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
            </td>
            </tr>
            </table>
    % endif
% endif
