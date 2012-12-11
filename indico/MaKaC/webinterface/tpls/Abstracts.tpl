<a href="" name="results"></a>
<table width="100%" valign="top" align="left" cellspacing="0">
    <tr>
        <td class="titleCellFormat" nowrap colspan="10">
            <form action=${ accessAbstract } method="post">
            ${ _("Quick search: Abstract ID")} <input type="text" name="abstractId" size="4"><input type="submit" class="btn" value="${ _("seek it")}"><br>
            </form>
        </td>
    </tr>
    <tr>
       <td nowrap colspan="11">
            <div class="CRLgroupTitleNoBorder">${ _("Displaying")}<strong> ${ filteredNumberAbstracts } </strong>
            % if filteredNumberAbstracts == "1":
                ${ _("abstract")}
            % else:
                ${ _("abstracts")}
            % endif
            % if filterUsed:
                (${ _("Total")}: <strong>${ totalNumberAbstracts }</strong>)
            % endif
            </div>
            <form action=${ filterPostURL } method="post" name="optionForm">
            <div class="CRLIndexList" >
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
            </div>
            </form>
        </td>
    </tr>
    <tr>
        <td colspan="11" align="left" width="100%">
          <form action=${ filterPostURL } method="post" name="displayOptionForm">
            <input type="hidden" name="operationType" value="display" />
            <div class="CRLDiv" style="display: none;" id="displayMenu">
                <table width="95%%" align="center" border="0">
                    <tr>
                        <td>
                            <table width="100%%">
                                <tr>
                                    <td>

                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <table align="center" cellspacing="0" width="100%%">
                                            <tr>
                                                <td style="border-bottom:1px solid lightgrey;" valign="top" align="left"><span style="color:black"><b>Columns to display:</b></span></td>
                                            </tr>
                                            <tr>
                                                <td align="left" class="titleCellFormat" style="padding-top:5px;" nowrap> <a id="selectDisplay">${_("Select all")}</a> | <a id="unselectDisplay">${_("Unselect all")}</a> </td>
                                            </tr>
                                            <tr>
                                                <td valign="top">${disp}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center"><input type="submit" class="btn" name="OK" value=  ${_("Apply")}></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </div>
          </form>
          ${ sortingOptions }
          <form action=${ filterPostURL } method="post" name="filterOptionForm" id="filterOptionForm">
            <input type="hidden" name="operationType" value="filter" />
            ${ filterMenu }
            ${ sortingOptions }
          </form>
        </td>
    </tr>
    <tr>
        <td colspan="11" style="border-bottom:2px solid #777777;padding-top:5px" valign="bottom" align="left">
        <form action=${abstractSelectionAction} method="post" name="abstractsForm" id="abstractsForm" onSubmit="return atLeastOneSelected()">
            <table>
                <tr>
                  <td colspan="10">
                      ${ displayOptions }
                  </td>
                </tr>
                <tr id="headPanel" class="follow-scroll" style="box-shadow: 0 4px 2px -2px rgba(0, 0, 0, 0.1);">
                    <td valign="bottom" width="100%" align="left" colspan="1000">
                        <table style="margin-left: -8px" >
                            <tr >
                                <td valign="bottom" align="left">
                                    <ul id="button-menu" class="ui-list-menu">
                                      <li class="left" id="addRegistrant">
                                        <a href="#" id="add_new_abstract">${_("Add new")}</a>
                                      </li>
                                      <li class="middle">
                                        <a href="#" id="accept_abstracts">${_("Accept")}</a>
                                      </li>
                                      <li class="middle">
                                        <a href="#" id="reject_abstracts">${_("Reject")}</a>
                                      </li>
                                      <li class="middle">
                                        <a href="#" id="merge_abstracts">${_("Merge")}</a>
                                      </li>
                                      <li class="middle">
                                        <a href="#" id="author_list">${_("Author list")}</a>
                                      </li>
                                      <li class="right">
                                        <a href="#" id="download_attachments">${_("Download attachments")}</a>
                                      </li>
                                    </ul>
                                </td>
                                <td>
                                  Export to:
                                </td>
                                <td>
                                    <input type="image" name="pdf" src=${ pdfIconURL} border="0">
                                    <input type="image" name="excel" src=${ excelIconURL } border="0">
                                    <input type="image" name="xml" src=${ xmlIconURL} border="0">
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    % if (totalNumberAbstracts == "0"):
    <tr>
        <td style="padding:15px 0px 15px 15px;"><span class="collShowBookingsText">${_("There are no abstracts submitted yet")}</span></td>
    </tr>
    % elif (filteredNumberAbstracts == "0"):
        <td style="padding:15px 0px 15px 15px;"><span class="collShowBookingsText">${_("There are no abstracts with the filters criteria selected")}</span></td>
    % else:
        <tr>
            <td colspan=4 style='padding: 5px 0px 10px;' nowrap>
            Select: <a style='color: #0B63A5;' id='selectAll'> All</a>, <a style='color: #0B63A5;' id='deselectAll'>None</a>
            </td>
        </tr>
        <tr>
            <td></td>
        </tr>
        <tr>
            <td></td>
        % if "ID" in displayColumns:
           <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #888;"><a href=${numberSortingURL}> ${_("ID")}</a>${numberImg}</td>
        % endif
        <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"> ${_("Title")}</td>
        % if "PrimaryAuthor" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"> ${_("Primary Author(s)")}</td>
        % endif
        % if "Tracks" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"> ${_("Tracks")}</td>
        % endif
        % if "Type" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href=${typeSortingURL}> ${_("Type")}</a>${typeImg}</td>
        % endif
        % if "Status" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href=${statusSortingURL}> ${_("Status")}</a>${statusImg}</td>
        % endif
        % if "Rating" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href=${ratingSortingURL}> ${_("Rating")}</a>${ratingImg}</td>
        % endif
        % if "AccTrack" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"> ${_("Acc. Track")}</td>
        % endif
        % if "AccType" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"> ${_("Acc. Type")}</td>
        % endif
        % if "SubmissionDate" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href=${dateSortingURL}> ${_("Submission date")}</a>${dateImg}</td>
        % endif
        </tr>
    % endif
    <tr><td>
        <tbody id="abstractsItems">
            ${ abstracts }
        </tbody>
    </td></tr>
</table>
</form>

<script type="text/javascript">
    var newAbst = false;

    function selectAllTracks() {
        $("#filterOptionForm #Tracks input:checkbox").attr("checked", true)
    }

    function unselectAllTracks() {
        $("#filterOptionForm #Tracks input:checkbox").attr("checked", false)
    }

    function selectAllTypes() {
        $("#filterOptionForm #Types input:checkbox").attr("checked", true)
    }

    function unselectAllTypes() {
        $("#filterOptionForm #Types input:checkbox").attr("checked", false)
    }

    function selectAllStatus() {
        $("#filterOptionForm #Status input:checkbox").attr("checked", true)
    };

    function unselectAllStatus() {
        $("#filterOptionForm #Status input:checkbox").attr("checked", false)
    }

    function selectAllAccTracks() {
        $("#filterOptionForm #AccTracks input:checkbox").attr("checked", true)
    }

    function unselectAllAccTracks() {
        $("#filterOptionForm #AccTracks input:checkbox").attr("checked", false)
    }

    function selectAllAccTypes() {
        $("#filterOptionForm #AccTypes input:checkbox").attr("checked", true)
    }

    function unselectAllAccTypes() {
        $("#filterOptionForm #AccTypes input:checkbox").attr("checked", false)
    }

    function atLeastOneSelected() {
        if(!newAbst) {
            var inputNodes = IndicoUtil.findFormFields($E("abstractsItems"))
            for (i = 0; i < inputNodes.length; i++)
            {
                var node = inputNodes[i];
                if (node.type == "checkbox") {
                    if(node.checked == true) {
                        return true;
                    }
                }
            }
            var dialog = new WarningPopup($T("Warning"), $T("No abstract selected! Please select at least one."));
            dialog.open();

            return false;
        } else {
            return true;
        }
    }

    function actionAbstractsRows() {
        $("tr[id^=abstracts] input:checkbox").click(function(){
            if(this.checked){
                $(this).parents('tr[id^=abstracts]').css('background-color',"#CDEB8B");
            }else{
                $(this).parents('tr[id^=abstracts]').css('background-color',"transparent");
            }
        });

        $("tr[id^=abstracts]").hover(function () {
            if($(this).find('input:checkbox:checked').size() == 0){
                $(this).css({'background-color' : 'rgb(255, 246, 223)'});
            }}
            , function () {
              if($(this).find('input:checkbox:checked').size() > 0){
                  $(this).css('background-color',"#CDEB8B");
              }else{
                  $(this).css('background-color',"transparent");
              }
        });
        $('tr[id^=abstracts] input:checkbox:checked').parents('tr[id^=abstracts]').css('background-color',"#CDEB8B");
    }

    function selectAll() {
        $('tr[id^=abstracts] input:checkbox').attr('checked', true);
        $('tr[id^=abstracts]').css('background-color',"#CDEB8B");
    }

    function deselectAll() {
        $('tr[id^=abstracts] input:checkbox').attr('checked', false);
        $('tr[id^=abstracts]').css('background-color',"transparent");
    }

    function showFilters() {
        if ($E("displayMenu").dom.style.display == "") { // Check if the other menu (columns) is shown and hide if needed
            $E("index_display").set('${ _("Select columns to display")}');
            $E('index_display').dom.className = "CRLIndexUnselected";
            $E("displayMenu").dom.style.display = "none";
        }
        if ($E("filterMenu").dom.style.display == "") { // the menu is shown, so hide it
% if filterUsed:
            $E("index_filter").set('${ _("Show filters")}');
% else:
            $E("index_filter").set('${ _("Apply filters")}');
% endif
            $E('index_filter').dom.className = "CRLIndexUnselected";
            $E("filterMenu").dom.style.display = "none";
        }else { // the menu is hiden so, show it
            $E("index_filter").set('${ _("Hide filters")}');
            $E('index_filter').dom.className = "CRLIndexSelected";
            $E("filterMenu").dom.style.display = "";
        }
    }

    function showDisplay() {
        if ($E("filterMenu").dom.style.display == "") { // Check if the other menu (filters) is shown and hide if needed
            % if filterUsed:
            $E("index_filter").set('${ _("Show filters")}')
            % else:
            $E("index_filter").set('${ _("Apply filters")}');
            % endif
            $E('index_filter').dom.className = "CRLIndexUnselected";
            $E("filterMenu").dom.style.display = "none";
        }
        if ($E("displayMenu").dom.style.display == "") { // the menu is shown, so hide it
            $E("index_display").set('${ _("Select columns to display")}');
            $E('index_display').dom.className = "CRLIndexUnselected";
            $E("displayMenu").dom.style.display = "none";
        }else { // the menu is hiden so, show it
            $E("index_display").set('${ _("Close selection")}');
            $E('index_display').dom.className = "CRLIndexSelected";
            $E("displayMenu").dom.style.display = "";
        }
    }

function showQuestionDetails(questions, answers) {
    // Create the table and the headers
    var content = Html.div();
    var table = Html.table({className:'infoQuestionsTable', cellspacing:'0'});
    content.append(table);
    var tbody = Html.tbody();
    table.append(tbody);
    var trHeaders = Html.tr();
    tbody.append(trHeaders);
    var tdQuestion = Html.td({className:'dataHeader'},'Question');
    var tdValues = Html.td({className:'dataHeader'},'Average');
    trHeaders.append(tdQuestion);
    trHeaders.append(tdValues);

    // Create the table with the required data
    var tr;
    var tdQ; // the question
    var tdA; // the answer
    for (var i=0; i < questions.length ; i++) {
        tr = Html.tr({className: 'infoTR'});
        tdQ = Html.td({className: 'content'}, questions[i]);
        tdA = Html.td({className: 'content'}, answers[i]);
        tbody.append(tr);
        tr.append(tdQ);
        tr.append(tdA);
    }

    popup = new AlertPopup('Average per question',content);
    popup.open();
}

IndicoUI.executeOnLoad(function(){

    actionAbstractsRows();
    $('#button-menu').dropdown();

    $(window).scroll(function(){
        IndicoUI.Effect.followScroll();
    });


    // Insert hidden field to the form
    var InsertHiddenField = function (name, value, cleanup){
        if (cleanup) {
            $("#abstractsForm input[type=hidden]").remove(); // clean previous actions
        }
        $('#abstractsForm').append($("<input>").attr("type", "hidden").attr("name", name).val(value));
    }

    $("#accept_abstracts").bind('menu_select',function(event) {
         InsertHiddenField("acceptMultiple", $T("Accept"), false);
         $('#abstractsForm').submit();
     });

    $("#reject_abstracts").bind('menu_select',function(event) {
        InsertHiddenField("rejectMultiple", $T("Reject"), false);
        $('#abstractsForm').submit();
     });

    $("#merge_abstracts").bind('menu_select',function(event) {
        InsertHiddenField("merge", $T("Merge"), false);
        $('#abstractsForm').submit();
     });

    $("#author_list").bind('menu_select',function(event) {
        InsertHiddenField("auth", $T("Author List"), false);
        $('#abstractsForm').submit();
     });

    $("#download_attachments").bind('menu_select',function(){
        InsertHiddenField("PKGA", $T("Download attachments"), false);
        $('#abstractsForm').submit();
    });

    $("#add_new_abstract").bind('menu_select',function(){
        newAbst = true;
        InsertHiddenField("newAbstract", $T("Add"), false);
        $('#abstractsForm').submit();
    });

    $("#selectDisplay").click(function(){
        $("#displayMenu input[type=checkbox]").attr("checked",true);
    });

    $("#unselectDisplay").click(function(){
        $("#displayMenu input[type=checkbox]").attr("checked",false);
    });

    $("#selectAll").click(function(){selectAll();});
    $("#deselectAll").click(function(){deselectAll();});

});

</script>
