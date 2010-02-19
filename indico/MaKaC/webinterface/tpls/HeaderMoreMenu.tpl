
<a><div id="moreMenu" class="dropDownMenuGrey" href="#"><%= _("More") %></div><div class="leftCorner"></div></a>


<form id="layoutForm" style="margin: 0px; display: inline">
    <input type="hidden" name="confId" value="<%= confId %>" />
    <input id="layoutFormInput" type="hidden" name="view" value="standard" />
</form>

<script type="text/javascript">

var moreMenu = $E('moreMenu');

var layoutForm = $E('layoutForm');
var layoutFormInput = $E('layoutFormInput');

var layoutMenuItems = {};
<% for item in viewoptions: %>
layoutMenuItems["<%= item['name']%>"] = function() {
    layoutFormInput.setAttribute('value', '<%= item['id'] %>');
    layoutForm.dom.submit();
}
<% end %>

moreMenu.observeClick(function(e) {
    var menuItems = {}
    var menu = new PopupMenu(menuItems, [moreMenu], <% if dark: %>'darkPopupList'<% end %><% else: %>null<% end %>);

    <% if showExportToICal: %>
    menuItems['<%= _("Export to iCal") %>'] = '<%= urlHandlers.UHConferenceToiCal.getURL(self._rh._conf) %>';
    <% end %>
    <% if showExportToPDF: %>
    menuItems['<%= _("Export to PDF") %>'] = '<%= pdfURL %>';
    <% end %>
    <% if showDLMaterial: %>
    menuItems['<%= _("Download material") %>'] = '<%= urlHandlers.UHConferenceDisplayMaterialPackage.getURL(self._rh._conf) %>';
    <% end %>
    <% if showLayout: %>
    menuItems['<%= _("Layout") %>'] = new PopupMenu(layoutMenuItems, [moreMenu, menu], <% if dark: %>'darkPopupList'<% end %><% else: %>null<% end %>);
    <% end %>

    var pos = moreMenu.getAbsolutePosition();
    menu.open(pos.x - 8, pos.y + 20);
    return false;
});

</script>
