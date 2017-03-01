<%page args="dark=None"/>
<%
if dark is not UNDEFINED:
    dark_ = dark
else:
    dark_ = False;

protection = getProtection(prot_obj) if prot_obj else None
%>

<div id="session-bar" class="${'ui-follow-scroll' if prot_obj and protection[0] != 'Public' else ''} session-bar${" session-bar-dark" if dark_ == True else ""}">
    <div class="toolbar right">
      <div class="group">
        % if prot_obj and not isFrontPage and (_session.user or protection[0] != 'Public'):
            <%include file="ProtectionWidget.tpl" args="protection=protection"/>
            <script type="text/javascript">
            $.ui.sticky({
                sticky: nothing,
                normal: nothing
            });
            </script>
        % endif
        <%include file="TimezoneSelector.tpl"/>
        % if _session.user:
        <%include file="SettingsWidget.tpl" args="Languages = Languages"/>
        % else:
        <%include file="LanguageSelector.tpl" args="Languages = Languages, IsHeader = False, dark=dark_"/>

        <%
            after_login_url = _request.values.get('next')
            if after_login_url is None and _request.endpoint != _app.config['MULTIPASS_LOGIN_ENDPOINT']:
                after_login_url = _request.relative_url
            if after_login_url == '/':
                after_login_url = None
        %>
        <a class="i-button icon-enter" href="${ url_for_login(after_login_url) }">${ _("Login")}</a>
        % endif
      </div>
    </div>
</div>
