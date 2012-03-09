<%page args="dark=None"/>
<%
if dark is not UNDEFINED:
    dark_ = dark
else:
    dark_ = False;
%>


<div class="sessionBar${" sessionBarDark" if dark_ == True else ""}">
    <div class="corner"></div>
    <div class="links">
        <ul>
            <li>
                <%include file="TimezoneSelector.tpl"/>
            </li>
            % if currentUser:
                <%include file="SettingsWidget.tpl" args="Languages = Languages, IsHeader = False, dark=dark_"/>
            % else:
                <%include file="LanguageSelector.tpl" args="Languages = Languages, IsHeader = False, dark=dark_"/>
                <li class="loginHighlighted" style="border-right: none;">
                    <a href="${ loginURL }"><strong style="color: white">${ _("Login")}</strong></a>
                </li>
            % endif
        </ul>
    </div>
</div>
