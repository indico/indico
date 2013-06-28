<table>
    <thead>
        <tr>
            <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">${ _('User')}</td>
            <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">${ _("Application")}</td>
            <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">${ _('Access Token')}</td>
            <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">${ _('Date')}</td>
            <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">${ _('Details')}</td>
        </tr>
    </thead>
    <tbody>
        % for token in tokens:
            <tr>
                <td class="CRLabstractDataCell">${token.getUser().getStraightFullName()}</td>
                <td class="CRLabstractDataCell">${token.getConsumer().getName()}</td>
                <td class="CRLabstractDataCell">${token.getUniqueId()}</td>
                <td class="CRLabstractDataCell">${formatTimestamp(token.getTimestamp())}</td>
                <td class="CRLabstractDataCell"><a href=${quoteattr(str(urlHandlers.UHOAuthUserThirdPartyAuth.getURL(token.getUser())))}>${_('Details')}</a></td>
            </tr>
        % endfor
    </tbody>
</table>
