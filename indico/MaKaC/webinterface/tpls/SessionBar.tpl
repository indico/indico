<%!
try:
    dark
except NameError:
    dark = False;
%>


<div class="sessionBar<% if dark == True: %> sessionBarDark<% end %>">
    <div class="corner"></div>
    <div class="links">
        <ul>
            <li>
                <% includeTpl('TimezoneSelector') %>
            </li>
            <li id="languageSelector">
                <% includeTpl('LanguageSelector', Languages = Languages, IsHeader = False, dark=dark) %>
            </li>
            <% includeTpl('LoginWidget') %>
        </ul>
    </div>
</div>