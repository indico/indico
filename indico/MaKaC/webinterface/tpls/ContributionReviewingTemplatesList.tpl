<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

    % if ConfReview.hasTemplates():
    <!-- here to put table for the uploaded templates info :) -->
    	<tr>
            <td nowrap width="20%" class="data">
                <span style="font-weight:bold;">${ _("Name")}</span>
            </td>
            <td nowrap width="20%" class="data">
                <span style="font-weight:bold;">${ _("Format")}</span>
            </td>
            <td nowrap width="33%" class="data">
                <span style="font-weight:bold;">${ _("Description")}</span>
            </td>
            <td nowrap width="27%" class="data" style="text-align:right;">
                <span style="font-weight:bold;">${ _("Actions")}</span>
            </td>
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
                <span class="link" onclick="window.location='${ urlHandlers.UHDownloadContributionTemplate.getURL(t) }';">${ _("Download") }</span>
            </td>
    	</tr>
    	% endfor
    % else:
        <tr><td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
            ${ _("No templates have been uploaded yet.")}
        </td></tr>

    % endif
