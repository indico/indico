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
                            <td>${key.user.getFullName()}</td>
                            <td>${key.use_count}</td>
                            <td>${formatDateTime(key.last_used_dt) if key.last_used_dt else _('Never')}</td>
                            <td>${_('Yes') if key.is_blocked else _('No')}</td>
                            <td>${ key.token }</td>
                            <td>
                                <a href="${urlHandlers.UHUserAPI.getURL(key.user)}">${_('Details')}</a>
                            </td>
                        </tr>
                    % endfor
                </tbody>
            </table>
        </td>
    </tr>
</table>
