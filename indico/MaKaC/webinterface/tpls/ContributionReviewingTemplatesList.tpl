<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

    % if ConfReview.hasTemplates():
    <!-- here to put table for the uploaded templates info :) -->
        <tr>
            <td nowrap width="20%" class="tableHeader">${ _("Name")}</td>
            <td nowrap width="20%" class="tableHeader">${ _("Format")}</td>
            <td nowrap width="33%" class="tableHeader">${ _("Description")}</td>
            <td nowrap width="27%" class="tableHeader" style="text-align:right;">${ _("Actions")}</td>
        </tr>

        <% keys = ConfReview.getTemplates().keys() %>
        <% keys.sort() %>
        % for k in keys:
            <% t = ConfReview.getTemplates()[k] %>
        <tr class="infoTR">
            <td class="content">
                ${ t.getName() }
            </td>
            <td class="content">
                ${ t.getFormat() }
            </td>
            <td class="content">
                ${ t.getDescription() }
            </td>
            <td class="content" style="text-align: right;">
                <a href="${ urlHandlers.UHDownloadPRTemplate.getURL(t) }">${ _("Download") }</a>
            </td>
        </tr>
        % endfor
    % else:
        <tr><td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
            ${ _("No templates have been uploaded yet.")}
        </td></tr>

    % endif
