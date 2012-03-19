<a href="" name="results"></a>
<table width="100%" cellspacing="0" align="center" border="0">
        <tr>
           <td nowrap colspan="10">
                <div class="CRLgroupTitleNoBorder">${ _("Displaying")}<strong> ${ filteredNumberRegistrants } </strong>
                    % if filteredNumberRegistrants == "1":
                        ${ _("registrant")}
                    % else:
                        ${ _("registrants")}
                    % endif
                    % if filterUsed:
                        (${ _("Total")}: <strong>${ totalNumberRegistrants }</strong>)
                    % endif
                </div>
                <form action=${ filterPostURL } method="post" name="optionForm">
                <div class="CRLIndexList" >
                    <br>
                    % if filterUsed:
                        <input type="submit" class="btnRemove" name="resetFilters" value="Reset filters">
                        <span style="padding: 0px 6px 0px 6px">|</span>
                    % endif
                    <a id="index_filter" onclick="showFilters()" class="CAIndexUnselected" font-size="16" font-weight="bold" font-family="Verdana">
                      % if filterUsed:
                        ${ _("Show filters")}
                      % else:
                        ${ _("Apply filters")}
                      % endif
                    </a>
                    <span style="padding: 0px 6px 0px 6px">|</span>
                    <a id="index_display" onclick="showDisplay()" class="CAIndexUnselected" font-size="16">
                        ${ _("Columns to display")}
                    </a>
                    <span style="padding: 0px 6px 0px 6px">|</span>
                    <a id="index_display" onclick="staticURLSwitch()" class="CAIndexUnselected" font-size="16">
                        ${ _("Static URL for this result")}
                    </a>
                </div>
                </form>
            </td>
        </tr>
        <tr nowrap colspan="10">
            <td colspan="1000" valign="bottom" align="left">
              <form action=${ filterPostURL } method="post" name="displayOptionForm">
                <input type="hidden" name="operationType" value="display" />
                ${ displayMenu }
                ${ sortingOptions }
              </form>
              <form action=${ filterPostURL } method="post" name="filterOptionForm">
                <input type="hidden" name="operationType" value="filter" />
                ${ filterMenu }
                ${ sortingOptions }
              </form>
            </td>
       </tr>

       <tr>
            <td colspan="1000" valign="bottom" align="left">
                <input type="text" id="staticURL" size="74" style="display: none;" readonly="readonly" value="${ filterUrl }" />
                <a id="staticURLLink" style="display: none; margin-left: 5px;" href="${ filterUrl }">${ _("Go to URL")}</a>
            </td>
       </tr>

        <tr>
          <td colspan="40" valign="bottom" align="left">
            <form id="registrantsForm" action=${ actionPostURL } method="post" name="registrantsForm" onsubmit="return atLeastOneRegistrantSelected();">
            <table width="100%" cellspacing="0" align="center" border="0">
                <tr>
                  <td colspan="10">
                    <div>
                      <input type="hidden" name="reglist" value="${ reglist }">
                      ${ displayOptions }
                    </div>
                  </td>
                </tr>
                 <tr id="headPanel" class="follow-scroll" style="box-shadow: 0 4px 2px -2px rgba(0, 0, 0, 0.1);">
                    <td valign="bottom" width="100%" align="left" colspan="1000">
                        <table style="margin-left: -8px" >
                            <tr >
                                <td valign="bottom" align="left">
                                    <ul id="button-menu" class="ui-list-menu">
                                      <li class="left" id="addRegistrant">
                                        <a href="#" id="add_new_user">${_("Add new")}</a>
                                      </li>
                                      <li class="middle">
                                        <a href="#" id="remove_users">${_("Remove")}</a>
                                      </li>
                                      <li class="middle">
                                        <a href="#" id="send_email">${_("Email")}</a>
                                      </li>
                                      <li class="middle">
                                        <a href="#" id="print_badges">${_("Print Badges")}</a>
                                      </li>
                                      <li class="middle">
                                        <a href="#" id="attachments">${_("Attachments")}</a>
                                      </li>
                                      <li class="right">
                                        <a href="#" id="show_stats">${_("Show stats")}</a>
                                      </li>
                                    </ul>
                                </td>

                                <td>
                                  Export to:
                                </td>
                                <td>
                                    <a href="#" id="exportPDFSelectorLink1" name="pdf" class="iconDropDownMenu"> <img src=${ pdfIconURL} border="0"></a>
                                    <input id="pdfExportInputHidden" type="hidden" name="pdf">
                                    <span class="iconSeparator">  | </span>
                                    <input type="image" style="margin-top:3px;" name="excel" src=${ excelIconURL } border="0">
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
              </table>
          </td>
        </tr>
        <tr nowrap colspan="10">
            % if filteredNumberRegistrants == "0":
            <tr id="noRegistrantInfo">
                <td colspan=10 style="font-style: italic; padding:15px 0px 15px 15px; border-bottom: 1px solid #DDDDDD;" nowrap>
                    <span class="collShowBookingsText">${ _("There are no registrants yet") }</span>
                </td>
            </tr>
            % else:
                ${ columns }
                <tbody id="registrantsItems">
                ${ registrants }
                </tbody>
            % endif
        </tr>
</table>
</form>

<script type="text/javascript">

var newUser = false;

<%include file="ListJSHelpers.tpl"/>


function selectDisplay()
{
    for (i = 0; i < document.displayOptionForm.disp.length; i++)
    {
        document.displayOptionForm.disp[i].checked=true;
    }
}

function unselectDisplay()
{
    for (i = 0; i < document.displayOptionForm.disp.length; i++)
    {
        document.displayOptionForm.disp[i].checked=false;
    }
}

function selectAll()
{
    if (!document.registrantsForm.registrant.length)
    {
        document.registrantsForm.registrant.checked=true;
    }else{
        for (i = 0; i < document.registrantsForm.registrant.length; i++)
        {
            document.registrantsForm.registrant[i].checked=true;
        }
    }
    isSelected("registrantsItems");
}

function deselectAll()
{
    if (!document.registrantsForm.registrant.length)
    {
        document.registrantsForm.registrant.checked=false;
    }else{
        for (i = 0; i < document.registrantsForm.registrant.length; i++)
        {
            document.registrantsForm.registrant[i].checked=false;
        }
    }
    isSelected("registrantsItems");
}


    function showFilters() {
        if ($E("displayMenu").dom.style.display == "") {
            $E("index_display").set('${ _("Select columns to display")}');
            $E('index_display').dom.className = "CRLIndexUnselected";
            $E("displayMenu").dom.style.display = "none";
        }
        if ($E("filterMenu").dom.style.display == "") {
% if filterUsed:
            $E("index_filter").set('${ _("Show filters")}');
% else:
            $E("index_filter").set('${ _("Apply filters")}');
% endif
            $E('index_filter').dom.className = "CRLIndexUnselected";
            $E("filterMenu").dom.style.display = "none";
        }else {
            $E("index_filter").set('${ _("Hide filters")}');
            $E('index_filter').dom.className = "CRLIndexSelected";
            $E("filterMenu").dom.style.display = "";
        }
    }
    function showDisplay() {
        if ($E("filterMenu").dom.style.display == "") {
% if filterUsed:
            $E("index_filter").set('${ _("Show filters")}');
% else:
            $E("index_filter").set('${ _("Apply filters")}');
% endif
           $E('index_filter').dom.className = "CRLIndexUnselected";
            $E("filterMenu").dom.style.display = "none";
        }
        if ($E("displayMenu").dom.style.display == "") {
            $E("index_display").set('${ _("Select columns to display")}');
            $E('index_display').dom.className = "CRLIndexUnselected";
            $E("displayMenu").dom.style.display = "none";
        }else {
            $E("index_display").set('${ _("Close selection")}');
            $E('index_display').dom.className = "CRLIndexSelected";
            $E("displayMenu").dom.style.display = "";
        }
    }

var pdfLink1 = $E('exportPDFSelectorLink1');
var pdfMenu = null;

function createMenu(pdfLink) {
    // Close the menu if clicking the link when menu is open
    if (pdfMenu != null && pdfMenu.isOpen()) {
        pdfMenu.close();
        pdfMenu = null;
        return;
    }

    // build a dictionary that represents the menu
    var menuItems = {};
    menuItems['tableStyle'] = {action: function () {submitForm("pdf.table");}, display: '${_("Table Style")}'};
    menuItems['bookStyle'] = {action: function () {submitForm("pdf.book");}, display: '${_("Book Style")}' };

    pdfMenu = new PopupMenu(menuItems, [pdfLink], null);
    var pos = pdfLink.getAbsolutePosition();
    pdfMenu.open(pos.x, pos.y + pdfLink.dom.offsetHeight + 3, null, null, false, true);
    return false;

}

function submitForm(style) {
    var form = $E('registrantsForm');
    var inputHidden = $E('pdfExportInputHidden');
    inputHidden.dom.name = style;
    if(form.dom.onsubmit())
        form.dom.submit(); pdfMenu.close();
}

pdfLink1.observeClick(function(e) {
    createMenu(pdfLink1);
    return false;
});

var atLeastOneRegistrantSelected = function(){
    if (newUser || $("input:checkbox:checked[name^=registrant]").length>0){
    return true;
    } else{
    var dialog = new WarningPopup($T("Warning"), $T("No registrant selected! Please select at least one."));
    dialog.open();
    return false;
    }
};

IndicoUI.executeOnLoad(function(){

% if filteredNumberRegistrants != "0":
    isSelected("registrantsItems");
% endif
    $('#button-menu').dropdown();

    $(window).scroll(function(){
        IndicoUI.Effect.followScroll();
    });


    // Insert hidden field to the form
    var InsertHiddenField = function (name, value, cleanup){
        if (cleanup) {
            $("#registrantsForm input[type=hidden]").remove(); // clean previous actions
        }
        $('#registrantsForm').append($("<input>").attr("type", "hidden").attr("name", name).val(value));
    }

    $("#print_badges").bind('menu_select',function(event) {
         InsertHiddenField("printBadgesSelected", "printBadges", false);
         $('#registrantsForm').submit();
     });

    $("#send_email").bind('menu_select',function(event) {
        InsertHiddenField("emailSelected", "True", false);
        $('#registrantsForm').submit();
     });

    $("#attachments").bind('menu_select',function(event) {
        InsertHiddenField("PKG", "attachments", false);
        $('#registrantsForm').submit();
     });

    $("#show_stats").bind('menu_select',function(event) {
        InsertHiddenField("info.x", "Show+stats", false);
        $('#registrantsForm').submit();
     });

    $("#remove_users").bind('menu_select',function(){
        InsertHiddenField("removeRegistrants", "remove", false);
        $('#registrantsForm').submit();
    });

    $("#add_new_user").bind('menu_select',function(){
        newUser = true;
        InsertHiddenField("newRegistrant", "Add", false);
        $('#registrantsForm').submit();
    });

});

</script>


