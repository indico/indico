<%page args="Languages=None, IsHeader=None, dark=None"/>

<li id="languageSelector">
    <form id="languageForm" method="post" action="${ urlHandlers.UHChangeLang.getURL() }" style="margin: 0px">
        <input id="languageInputHidden" type="hidden" name="lang" value="${ SelectedLanguage.lower() }">
    </form>
    <a id="languageSelectorLink" href="#" class="dropDownMenu" id="selectLanguageLink">${ SelectedLanguageName }</a>
</li>

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
    % for k,v in Languages:
        menuItems['${ v }'] = {action:function() {inputHidden.dom.value = '${ k }'; form.dom.submit()}, display:'${ v }'};
    % endfor

    languageMenu = new PopupMenu(menuItems, [languageLink], ${"'darkPopupList'" if dark else "null"}, true, true);
    var pos = languageLink.getAbsolutePosition();
    languageMenu.open(pos.x + languageLink.dom.offsetWidth + 10, pos.y + languageLink.dom.offsetHeight + 3, null, null, false, true);

    return false;
});
</script>
