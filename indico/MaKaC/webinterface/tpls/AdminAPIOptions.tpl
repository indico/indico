<form method="POST" action="${urlHandlers.UHAdminAPIOptionsSet.getURL()}">
    <table class="groupTable">
        <tr>
            <td>
                <div class="groupTitle">${ _("API Options") }</div>
            </td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat">HTTPS</span></td>
            <td class="blacktext">
                <input type="checkbox" name="httpsRequired" id="httpsRequired" value="1"${' checked="checked"' if httpsRequired else ''} />
                <label for="httpsRequired">${ _("Require HTTPS for authenticated API requests")}</label>
            </td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat">Persistent signatures</span></td>
            <td class="blacktext">
                <input type="checkbox" name="persistentAllowed" id="persistentAllowed" value="1"${' checked="checked"' if persistentAllowed else ''} />
                <label for="persistentAllowed">${ _("Allow users to enable persistent signatures (without timestamp)")}</label>
            </td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("API mode")}</span></td>
            <td class="blacktext">
                <select name="apiMode">
                    <option value="0"${' selected="selected"' if apiMode == 0 else ''}>${ _("Public requests without API key, authenticated requests with API key") }</option>
                    <option value="1"${' selected="selected"' if apiMode == 1 else ''}>${ _("All requests require an API key") }</option>
                    <option value="2"${' selected="selected"' if apiMode == 2 else ''}>${ _("Public requests without API key, authenticated requests with API key and signature") }</option>
                    <option value="3"${' selected="selected"' if apiMode == 3 else ''}>${ _("All requests require an API key, authenticated requests additionally need a signature") }</option>
                    <option value="4"${' selected="selected"' if apiMode == 4 else ''}>${ _("All requests require an API key and a signature") }</option>
                </select>
            </td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Cache TTL (seconds)") }</span></td>
            <td class="blacktext">
                <input type="text" name="apiCacheTTL" id="apiCacheTTL" value="${apiCacheTTL}" />
            </td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Signature TTL (seconds)") }</span></td>
            <td class="blacktext">
                <input type="text" name="apiSignatureTTL" id="apiSignatureTTL" value="${apiSignatureTTL}" />
            </td>
        </tr>
        <tr>
            <td></td>
            <td><input type="submit" value="${_('Save')}" /></td>
        </tr>
    </table>
</form>
