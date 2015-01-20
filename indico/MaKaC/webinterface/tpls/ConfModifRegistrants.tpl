<a href="" name="results"></a>
<table style="margin-top: 1em; border-spacing: 0; border-collapse: collapse; width: 100%;">
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
                    <a id="index_filter" onclick="showFilters()" class="CRLIndexUnselected" font-size="16" font-weight="bold" font-family="Verdana">
                      % if filterUsed:
                        ${ _("Show filters")}
                      % else:
                        ${ _("Apply filters")}
                      % endif
                    </a>
                    <span style="padding: 0px 6px 0px 6px">|</span>
                    <a id="index_display" onclick="showDisplay()" class="CRLIndexUnselected" font-size="16">
                        ${ _("Columns to display")}
                    </a>
                    <span style="padding: 0px 6px 0px 6px">|</span>
                    <a id="index_display" onclick="staticURLSwitch()" class="CRLIndexUnselected" font-size="16">
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
            <input id="pdfExportInputHidden" type="hidden" name="pdf">
            <table>
                <tr>
                  <td colspan="10">
                    <div>
                      <input type="hidden" name="reglist" value="${ reglist }">
                      ${ displayOptions }
                    </div>
                  </td>
                </tr>
                 <tr id="headPanel" class="follow-scroll">
                    <td valign="bottom" width="100%" align="left" colspan="1000">
                        <table style="margin-left: -8px;">
                            <tr >
                                <td valign="bottom" align="left" id="button-menu" class="toolbar" style="padding-bottom: 1em;">

                                  <div class="group left">
                                    <a class="icon-checkbox-checked i-button arrow left icon-only" aria-hidden="true" href="#" title="${_("Select")}" data-toggle="dropdown"></a>
                                    <ul class="dropdown">
                                      <li><a href="#" id="selectAll">All</a></li>
                                      <li><a href="#" id="selectNone">None</a></li>
                                    </ul>
                                  </div>

                                  <div class="group left">
                                    <a href="#" class="i-button" id="add_new_user">${_("Add new")}</a>
                                    <a href="#" class="i-button" id="remove_users">${_("Remove")}</a>
                                    % if eTicketEnabled:
                                    <a href="#" class="i-button" id="check_in">${_("Check in")}</a>
                                    % endif
                                    <a href="#" class="i-button" id="send_email">${_("Email")}</a>
                                    <a href="#" class="i-button" id="print_badges">${_("Print Badges")}</a>
                                    <a href="#" class="i-button" id="attachments">${_("Attachments")}</a>
                                    <a href="#" class="i-button" id="show_stats">${_("Show stats")}</a>
                                    <a class="i-button arrow button" href="#" data-toggle="dropdown">
                                      ${_("Export")}
                                    </a>
                                    <ul class="dropdown">
                                      <li><a href="#" class="icon-file-pdf" id="export_pdf">${_("PDF")}</a></li>
                                      <li><a href="#" class="icon-file-excel" id="export_csv">${_("CSV")}</a></li>
                                    </ul>
                                  </div>

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
                    <span class="italic">${ _("There are no registrants yet") }</span>
                </td>
            </tr>
            % else:
                ${ columns }

                <tbody id="registrantsItems">

                  % for reg, regdict in registrants:

                    <tr id="registrant${reg.getId()}" style="background-color: transparent;" onmouseout="javascript:onMouseOut('registrant${reg.getId()}')"
                        onmouseover="javascript:onMouseOver('registrant${reg.getId()}')">
                      <td style="width: 1.5em;">
                        <input onchange="javascript:isSelected('registrant${reg.getId()}')" type="checkbox" name="registrant" value="${reg.getId()}"/>
                      </td>
                      % if "Id" in groups_order["PersonalData"]:
                        <td class="CRLabstractLeftDataCell">${reg.getId()}</td>
                      % endif

                       <td nowrap class="CRLabstractDataCell"><a href="${urlHandlers.UHRegistrantModification.getURL(reg)}">${reg.getFullName()}</a></td>

                      % for key in groups_order["PersonalData"]:
                        % if key != "Name" and key != "Id":
                          <td class="CRLabstractDataCell">${regdict[key]}</td>
                        % endif
                      % endfor

                      % for group_key, group_data in groups_order.iteritems():
                        % if group_key != "PersonalData":
                          % for key in group_data:
                            % if key == "checkedIn":
                                <td class="CRLabstractDataCell checkedIn">
                                    ${regdict[key]}
                                </td>
                            % elif key == "checkInDate":
                                <td class="CRLabstractDataCell checkInDate">
                                    ${regdict[key]}
                                </td>
                            % else:
                                <td class="CRLabstractDataCell">
                                    ${regdict[key]}
                                </td>
                            % endif
                          % endfor
                        % endif
                      % endfor
                    </tr>
                  % endfor
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

var pdfLink1 = $E('export_pdf');
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

function getSelectedRegistrants() {
    var selected = new Array();
    $("input[name='registrant']:checked").each(function() {
        selected.push($(this).val());
    });
    return selected;
}

var atLeastOneRegistrantSelected = function(){
    if (newUser || getSelectedRegistrants().length > 0){
        return true;
    } else {
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

   $("#export_pdf").on("menu_select", function() {
      createMenu(pdfLink1);
      return true;
   });

   $("#export_csv").on("menu_select", function() {
      submitForm('excel');
   });

    $("#check_in").bind('menu_select',function(){
        if (atLeastOneRegistrantSelected()) {
            var selectedRegistrants = getSelectedRegistrants();
            var killProgress = IndicoUI.Dialogs.Util.progress($T("Checking in registrants..."));
            indicoRequest("registration.eticket.checkin",
                {
                    registrants: selectedRegistrants,
                    conference: "${ conferenceId }",
                },
                function(result, error){
                    if (!error) {
                        killProgress();
                        dates = result["dates"]
                        for(var id in dates){
                            changedFieldCheckedIn = $("input[value=" + id + "]")
                                                    .parents("td")
                                                    .nextAll("td.checkedIn");
                            changedFieldCheckedIn.effect("highlight", {}, 1500);
                            changedFieldCheckedIn.html("${_('Yes')}");
                            changedFieldCheckInDate = $("input[value=" + id + "]")
                                                      .parents("td")
                                                      .nextAll("td.checkInDate");
                            changedFieldCheckInDate.effect("highlight", {}, 1500);
                            changedFieldCheckInDate.html(dates[id]);
                        }
                    } else {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
            );
        }
    });

    $('#selectAll').click(function() {
        $('#registrantsItems input:visible').prop('checked', true).trigger('change');
    });

    $('#selectNone').click(function() {
        $('#registrantsItems input:visible').prop('checked', false).trigger('change');
    });

    $("#registrantsItems input:visible").on('change', function(){
        $(this).closest('tr').toggleClass('selected', this.checked);
    });
});

</script>


