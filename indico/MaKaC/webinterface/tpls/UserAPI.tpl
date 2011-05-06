<table class="groupTable">
    <tr>
        <td colspan="2">
            <div class="groupTitle">${ _("HTTP API details") }</div>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("API Key")}</span></td>
        <td class="blacktext">
            ${apiKey.getKey() if apiKey else _('None')}
            % if apiKey and apiKey.isBlocked():
                <span class="warningText">Blocked ${inlineContextHelp(_('Your API key has been blocked. Please contact an administrator for details.'))}</span>
            % endif
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Created")}</span></td>
        <td class="blacktext">
            ${formatDateTime(apiKey.getCreatedDT()) if apiKey else _('n/a')}
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Last used")}</span></td>
        <td class="blacktext">
            ${apiKey.getLastUsedDT() and formatDateTime(apiKey.getLastUsedDT()) or 'Never' if apiKey else _('n/a')}
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Last used by")}</span></td>
        <td class="blacktext">
            ${apiKey.getLastUsedIP() or 'n/a' if apiKey else _('n/a')}
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Last request")}</span></td>
        <td class="blacktext">
            ${apiKey.getLastRequest() or 'n/a' if apiKey else _('n/a')}
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Total uses")}</span></td>
        <td class="blacktext">
            ${apiKey.getUseCount() if apiKey else _('n/a')}
        </td>
    </tr>
    % if not apiKey or not apiKey.isBlocked():
        <tr>
            <td></td>
            <td>
                % if not apiKey:
                    <form action="${urlHandlers.UHUserAPICreate.getURL(avatar)}" method="POST" onsubmit="return confirm('${_("Please only create an API key if you actually need one. Unused API keys might be deleted after some time.")}');">
                        <input type="submit" value="Create API key" />
                    </form>
                % else:
                    <form action="${urlHandlers.UHUserAPICreate.getURL(avatar)}" method="POST" onsubmit="return confirm('${_("Warning: When creating a new API key, your old key will stop working immediately!")}');">
                        <input type="submit" value="Create a new API key" />
                    </form>
                % endif
            </td>
        </tr>
    % endif

    % if isAdmin:
        <tr>
            <td colspan="2">
                <div class="groupTitle">${ _("Administration") }</div>
            </td>
        </tr>
        % if apiKey:
            <tr>
                <td></td>
                <td>
                    <form action="${urlHandlers.UHUserAPIBlock.getURL(avatar)}" method="POST">
                        <input type="submit" value="${_('Unblock API key') if apiKey.isBlocked() else _('Block API key')}" />
                    </form>
                </td>
            </tr>
        % endif
    % endif
</table>
