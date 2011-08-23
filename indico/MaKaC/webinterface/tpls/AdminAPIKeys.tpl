<table class="groupTable">
    <tr>
        <td>
            <div class="groupTitle">${ _("API Keys") }</div>
        </td>
    </tr>
    <tr>
        <td>
            <table cellpadding="3">
                <thead>
                    <tr>
                        <td class="dataCaptionFormat">${ _("User")}</td>
                        <td class="dataCaptionFormat">${ _('Uses')}</td>
                        <td class="dataCaptionFormat">${ _('Last used')}</td>
                        <td class="dataCaptionFormat">${ _("Blocked")}</td>
                        <td class="dataCaptionFormat">${ _("API Key")}</td>
                        <td class="dataCaptionFormat">${ _("Actions")}</td>
                    </tr>
                </thead>
                <tbody>
                    % for key in apiKeys:
                        <tr>
                            <td>${key.getUser().getFullName()}</td>
                            <td>${key.getUseCount()}</td>
                            <td>${formatDateTime(key.getLastUsedDT()) if key.getLastUsedDT() else _('Never')}</td>
                            <td>${_('Yes') if key.isBlocked() else _('No')}</td>
                            <td>${ key.getKey() }</td>
                            <td>
                                <a href="${urlHandlers.UHUserAPI.getURL(key.getUser())}">${_('Details')}</a>
                            </td>
                        </tr>
                    % endfor
                </tbody>
            </table>
        </td>
    </tr>
</table>
