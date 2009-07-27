
<a><div id="moreMenu" class="dropDownMenuGrey" href="#"><%= _("More") %></div><div class="leftCorner"></div></a>

<script type="text/javascript">
var moreMenu = $E('moreMenu');
moreMenu.observeClick(function(e) {
    var menuItems = {'<%= _("Export to iCal") %>': '<%= urlHandlers.UHConferenceToiCal.getURL(self._rh._conf) %>',
                     <% if showExportToPDF: %>'<%= _("Export to PDF") %>': <%= pdfURL %>,<% end %>
                     '<%= _("Download material") %>': '<%= urlHandlers.UHConferenceDisplayMaterialPackage.getURL(self._rh._conf) %>'
                     //'<%= _("Layout") %>': function(){alert('layout!');}
                    };

    var menu = new PopupMenu(menuItems, [moreMenu], <% if dark: %>'darkPopupList'<% end %><% else: %>null<% end %>);
    var pos = moreMenu.getAbsolutePosition();
    menu.open(pos.x - 8, pos.y + 20);
    return false;
});
</script>
