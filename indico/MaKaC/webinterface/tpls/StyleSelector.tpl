
<a><div id="layoutMenu" class="dropDownMenuGrey" href="#">${ _("Layout") }</div><div class="leftCorner"></div></a>


<form id="layoutForm" style="margin: 0px; display: inline">
    <input type="hidden" name="confId" value="${ confId }" />
    <input id="layoutFormInput" type="hidden" name="view" value="standard" />
</form>

<script type="text/javascript">
var layoutMenu = $E('layoutMenu');
var layoutForm = $E('layoutForm');
var layoutFormInput = $E('layoutFormInput');
layoutMenu.observeClick(function(e) {
    var menuItems = {};

    % for item in viewoptions: 
    menuItems["${ item['name']}"] = function() {
        layoutFormInput.setAttribute('value', '${ item['id'] }');
        layoutForm.dom.submit();
    }
    % endfor

    var menu = new PopupMenu(menuItems, [layoutMenu], ${"'darkPopupList'" if dark else "null"});
    var pos = layoutMenu.getAbsolutePosition();
    menu.open(pos.x - 8, pos.y + 20);
    return false;
});
</script>
