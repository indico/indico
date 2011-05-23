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
    % if signingEnabled:
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Secret Key")}</span></td>
            <td class="blacktext">
                ${apiKey.getSignKey() if apiKey else _('None')}
                ${inlineContextHelp(_('To use your API key you must sign &quot;Path?QueryString&TS&quot; (TS=int(UnixTimestamp/300)) using HMAC-SHA1 and append it to the query string, e.g. &quot;Path?QueryString&SignatureHash&quot;'))}
            </td>
        </tr>
    % endif
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
            % if apiKey and apiKey.getLastRequest():
                ${escape(apiKey.getLastRequest())} (${_('Authenticated') if apiKey.isLastUseAuthenticated() else 'Public'})
            % else:
                ${_('n/a')}
            % endif
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
                        <input type="submit" value="${_('Create API key')}" />
                    </form>
                % else:
                    <form action="${urlHandlers.UHUserAPICreate.getURL(avatar)}" method="POST" onsubmit="return confirm('${_("Warning: When creating a new API key pair, your old key pair will stop working immediately!")}');">
                        <input type="submit" value="${_('Create a new API key pair')}" />
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
                    <form action="${urlHandlers.UHUserAPIBlock.getURL(avatar)}" method="POST" style="display:inline;">
                        <input type="submit" value="${_('Unblock API key') if apiKey.isBlocked() else _('Block API key')}" />
                    </form>

                    <form action="${urlHandlers.UHUserAPIDelete.getURL(avatar)}" method="POST" style="display:inline;" onsubmit="return confirm('${_("Do you really want to DELETE the API key? The user will be able to create a new key, but all history will be lost.")}');">
                        <input type="submit" value="${_('Delete API key')}" />
                    </form>
                </td>
            </tr>
            <tr>
                 <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">Old keys</span></td>
                 <td class="blacktext">
                    % if apiKey.getOldKeys():
                        <ul>
                            % for key in apiKey.getOldKeys():
                                <li>${key}</li>
                            % endfor
                        </ul>
                    % else:
                        None
                    % endif
                 </td>
             </tr>
        % else:
            <tr>
                <td colspan="2" class="blacktext">
                    ${_('No actions available')}
                </td>
            </tr>
        % endif
    % endif
</table>
