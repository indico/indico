<%page args="dark=None"/>
<%
if dark is not UNDEFINED:
    dark_ = dark
else:
    dark_ = False;

protection = getProtection(target) if target else None
%>

<div id="session-bar" class="${'ui-follow-scroll' if target and protection[0] != 'Public' else ''} session-bar${" session-bar-dark" if dark_ == True else ""}">
    <div class="toolbar right">
      <div class="group">
        % if target and protection[0] != "Public":
            <%include file="ProtectionWidget.tpl" args="protection=protection"/>
            <script type="text/javascript">
            $.ui.sticky({
                sticky: nothing,
                normal: nothing
            });
            </script>
        % endif
        <%include file="TimezoneSelector.tpl"/>
        % if currentUser:
        <%include file="SettingsWidget.tpl" args="Languages = Languages"/>
        % else:
        <%include file="LanguageSelector.tpl" args="Languages = Languages, IsHeader = False, dark=dark_"/>
        <a class="i-button icon-enter" href="${ loginURL }">${ _("Login")}</a>
        % endif
      </div>
    </div>
</div>
