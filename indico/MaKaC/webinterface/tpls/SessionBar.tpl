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
            <li id="languageSelector">
                <%include file="LanguageSelector.tpl" args="Languages = Languages, IsHeader = False, dark=dark_"/>
            </li>
            <%include file="LoginWidget.tpl"/>
        </ul>
    </div>
</div>