<%page args="viewoptions=None, SelectedStyle=None, pdfURL=None, showExportToPDF=None, showDLMaterial=None, showLayout=None, displayURL=None"/>

<a><div id="moreMenu" class="dropDownMenuGrey" href="#">${ _("More") }</div><div class="leftCorner"></div></a>

<form id="layoutForm" action="${ displayURL }" style="margin: 0px; display: inline">
    <input id="layoutFormInput" type="hidden" name="view" value="standard" />
</form>

<script type="text/javascript">

var moreMenu = $E('moreMenu');

var layoutForm = $E('layoutForm');
var layoutFormInput = $E('layoutFormInput');

var layoutMenuItems = {};
% for item in viewoptions:
layoutMenuItems["${ item['id']}"] = {action: function() {
    layoutFormInput.setAttribute('value', '${ item['id'] }');
    layoutForm.dom.submit();
}, display: "${ item['name']}"};
% endfor

moreMenu.observeClick(function(e) {
    var menuItems = {}
    var menu = new PopupMenu(menuItems, [moreMenu], ${"'darkPopupList'" if dark else "null"});

    % if showExportToPDF:
    menuItems["exportPDF"] = {action: '${ pdfURL }', display: "${ _('Export to PDF') }"};
    % endif
    % if showDLMaterial:
    menuItems["downloadMaterial"] = {action: '${ urlHandlers.UHConferenceDisplayMaterialPackage.getURL(self_._rh._conf) }', display: "${ _('Download material') }"};
    % endif
    % if showLayout:
    menuItems["layout"] = {action: new PopupMenu(layoutMenuItems, [moreMenu, menu], ${"'darkPopupList'" if dark else "null"}, null, null, null, '${ SelectedStyle }'), display: "${ _('Layout') }"};
    % endif

    var pos = moreMenu.getAbsolutePosition();
    menu.open(pos.x - 8, pos.y + 20);
    return false;
});




</script>
