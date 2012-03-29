<%page args="dark=None"/>
<%
if dark is not UNDEFINED:
    dark_ = dark
else:
    dark_ = False;

protection = getProtection(target) if target else None
%>

<div id="sessionBar" class="${'ui-follow-scroll' if target and protection[0] != 'Public' else ''} sessionBar${" sessionBarDark" if dark_ == True else ""}">
    % if not target or protection == "Public":
        <div class="corner"></div>
    % else:
        <div class="corner corner${protection[0]}"></div>
    % endif
    <div class="links">
        <ul>
            % if target and protection[0] != "Public":
                <%include file="ProtectionWidget.tpl" args="protection=protection"/>
                <script type="text/javascript">
                $.ui.sticky({
                    sticky: nothing,
                    normal: nothing
                });
                </script>
            % endif
            <li>
                <%include file="TimezoneSelector.tpl"/>
            </li>
            % if currentUser:
                <%include file="SettingsWidget.tpl" args="Languages = Languages"/>
            % else:
                <%include file="LanguageSelector.tpl" args="Languages = Languages, IsHeader = False, dark=dark_"/>
                <li class="loginHighlighted" style="border-right: none;">
                    <a href="${ loginURL }"><strong style="color: white">${ _("Login")}</strong></a>
                </li>
            % endif
        </ul>
    </div>
</div>