<%page args="viewoptions=None, SelectedStyle=None, pdfURL=None, showExportToICal=None, showExportToPDF=None, showDLMaterial=None, showLayout=None, displayURL=None"/>

<a><div id="moreMenu" class="dropDownMenuGrey" href="#">${ _("More") }</div><div class="leftCorner"></div></a>


<form id="layoutForm" action="${ displayURL }" style="margin: 0px; display: inline">
    <input type="hidden" name="confId" value="${ confId }" />
    <input id="layoutFormInput" type="hidden" name="view" value="standard" />
</form>

<script type="text/javascript">

var moreMenu = $E('moreMenu');

var layoutForm = $E('layoutForm');
var layoutFormInput = $E('layoutFormInput');

var layoutMenuItems = {};
% for item in viewoptions:
layoutMenuItems["${ item['name']}"] = function() {
    layoutFormInput.setAttribute('value', '${ item['id'] }');
    layoutForm.dom.submit();
}
% endfor

moreMenu.observeClick(function(e) {
    var menuItems = {}
    var menu = new PopupMenu(menuItems, [moreMenu], ${"'darkPopupList'" if dark else "null"});

    % if showExportToICal:
    menuItems['${ _("Export event to iCal") }'] = '${ urlHandlers.UHConferenceToiCal.getURL(self_._rh._conf, detailLevel = "top") }';
    menuItems['${ _("Export timetable to iCal") }'] = '${ urlHandlers.UHConferenceToiCal.getURL(self_._rh._conf, detailLevel = "contributions") }';
    % endif
    % if showExportToPDF:
    menuItems['${ _("Export to PDF") }'] = '${ pdfURL }';
    % endif
    % if showDLMaterial:
    menuItems['${ _("Download material") }'] = '${ urlHandlers.UHConferenceDisplayMaterialPackage.getURL(self_._rh._conf) }';
    % endif
    % if showLayout:
    menuItems['${ _("Layout") }'] = new PopupMenu(layoutMenuItems, [moreMenu, menu], ${"'darkPopupList'" if dark else "null"}, null, null, null, '${ SelectedStyle }');
    % endif

    var pos = moreMenu.getAbsolutePosition();
    menu.open(pos.x - 8, pos.y + 20);
    return false;
});

</script>
