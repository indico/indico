<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

% if User is not None:
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
                    ${ c.id }
                </td>
                <td class="content" valign="top">
                    ${ c.title }
                </td>
                % if Conference.getConfPaperReview().hasReviewing():
                <td class="content" valign="top">
                    ${"<br>".join(Conference.getReviewManager(c).getLastReview().getReviewingStatus(forAuthor = True))}
                </td>
                % endif
                <td nowrap class="content" valign="top" style="text-align: right;">
                % if c.can_manage(_session.user):
                    <a href="${ url_for('contributions.manage_contributions', c, selected=c.friendly_id) }">${ _("Edit") }</a>
                    <span class="horizontalSeparator">|</span>
                    <a href="${ url_for('contributions.display_contribution', c) }">${ _("View") }</a>
                % else:
                    <a href="${ url_for('contributions.display_contribution', c) }">${ _("Upload Paper") }</a>
                % endif
                </td>
            </tr>
            % endfor
        </table>
    % endif
% endif
