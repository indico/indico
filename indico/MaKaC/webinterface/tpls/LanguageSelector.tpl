

            <form id="languageForm" method="post" action="<%= urlHandlers.UHChangeLang.getURL() %>" style="margin: 0px">
                <input id="languageInputHidden" type="hidden" name="lang" value="<%= SelectedLanguage.lower() %>">
            </form>

        
<a id="languageSelectorLink" href="#" class="dropDownMenu" id="selectLanguageLink"><%= SelectedLanguageName %></a>

        
<script type="text/javascript">
var languageLink = $E('languageSelectorLink');
var languageMenu = null;
languageLink.observeClick(function(e) {
    // Close the menu if clicking the link when menu is open
    if (languageMenu != null && languageMenu.isOpen()) {
        languageMenu.close();
        languageMenu = null;
        return;
    }
    
    var menuItems = {};
    var form = $E('languageForm');
    var inputHidden = $E('languageInputHidden');
            
    // build a dictionary that represents the menu
    <% for k,v in Languages.items(): %>
        menuItems['<%= v %>'] = function() {inputHidden.dom.value = '<%= k %>'; form.dom.submit()};
    <% end %>
        
    languageMenu = new PopupMenu(menuItems, [languageLink], <% if dark: %>'darkPopupList'<% end %><% else: %>null<% end %>, true, true);
    var pos = languageLink.getAbsolutePosition();
    languageMenu.open(pos.x + languageLink.dom.offsetWidth + 10, pos.y + languageLink.dom.offsetHeight + 3, null, null, false, true);

    return false;
});
</script>