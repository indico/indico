<%def name="includeOrderImg(column='')">
   % if sortingField == column:
        % if order == "down":
            <img src="${downArrow}" alt="down">
        % elif order == "up":
            <img src="${upArrow}" alt="up">
        % endif
   % endif
</%def>


<a href="" name="results"></a>
<table width="100%" valign="top" align="left" cellspacing="0">
    <tr>
        <td class="titleCellFormat" nowrap colspan="12">
            <form action=${ accessAbstract } method="post">
            ${ _("Quick search: Abstract ID")} <input type="text" name="abstractId" size="4"><input type="submit" value="${ _("seek it")}"><br>
            </form>
        </td>
    </tr>
    <tr>
       <td nowrap colspan="12">
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
                <a id="index_filter" class="CRLIndexUnselected" font-size="16" font-weight="bold" font-family="Verdana">
                  % if filterUsed:
                    ${ _("Show filters")}
                  % else:
                    ${ _("Apply filters")}
                  % endif
                </a>
                <span style="padding: 0px 6px 0px 6px">|</span>
                <a id="index_display" class="CRLIndexUnselected" font-size="16">
                    ${ _("Columns to display")}
                </a>
            </div>
            </form>
        </td>
    </tr>
    <tr>
        <td colspan="12" align="left" width="100%">
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
                                                <td valign="top">
                                                    <table width="100%%" cellpadding="0" cellspacing="0" valign="top">
                                                        % for column in columns:
                                                            <tr>
                                                                <td align="left" valign="top">
                                                                    %if column == 'Title':
                                                                        <input type="hidden" name="disp" value="${column}">
                                                                    %endif
                                                                    <input type="checkbox" name="disp" value="${column}" ${"checked" if column in displayColumns or  column == 'Title' else ""}  ${"disabled" if column == 'Title' else ""}>

                                                                </td>
                                                                <td width="100%%" align="left" valign="top">${columnsDict[column]}
                                                                </td>
                                                            </tr>
                                                        %endfor
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center"><input type="submit" class="i-button" name="OK" value=  ${_("Apply")}></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </div>
            <input type="hidden" name="sortBy" value="${sortingField}">
            <input type="hidden" name="order" value="${order}">
          </form>
          <form action=${ filterPostURL } method="post" name="filterOptionForm" id="filterOptionForm">
            <input type="hidden" name="operationType" value="filter" />
            ${ filterMenu }
            <input type="hidden" name="sortBy" value="${sortingField}">
            <input type="hidden" name="order" value="${order}">
          </form>
        </td>
    </tr>
    <tr>
        <td colspan="12" style="padding-top:5px" valign="bottom" align="left">
        <form action=${abstractSelectionAction} method="post" name="abstractsForm" id="abstractsForm">
            <table>
                <tr>
                  <td colspan="10">
                    % for option in displayColumns:
                        <input type="hidden" name="disp" value="${option}">
                    % endfor
                    <input type="hidden" name="order" value="${order}">
                  </td>
                </tr>
                <tr id="headPanel" class="follow-scroll">
                    <td valign="bottom" width="100%" align="left" colspan="1000">
                        <table style="margin-left: -8px" >
                            <tr >
                                <td valign="bottom" align="left">
                                    <div id="button-menu" class="toolbar">

                                      <div class="group left">
                                        <a class="icon-checkbox-checked i-button arrow left icon-only" aria-hidden="true" href="#" title="${_("Select")}" data-toggle="dropdown"></a>
                                        <ul class="dropdown">
                                          <li><a href="#" id="selectAll">All</a></li>
                                          <li><a href="#" id="selectNone">None</a></li>
                                        </ul>
                                      </div>

                                      <div class="group left">
                                        <a href="#" id="add_new_abstract" class="i-button">${_("Add new")}</a>
                                        <a href="#" id="accept_abstracts" class="i-button">${_("Accept")}</a>
                                        <a href="#" id="reject_abstracts" class="i-button">${_("Reject")}</a>
                                        <a href="#" id="merge_abstracts" class="i-button">${_("Merge")}</a>
                                        <a href="#" id="author_list" class="i-button">${_("Author list")}</a>
                                        <a href="#" id="download_attachments" class="i-button">${_("Download attachments")}</a>

                                        <a class="i-button arrow" href="#" data-toggle="dropdown">
                                          ${_("Export")}
                                        </a>
                                        <ul class="dropdown">
                                          <li><a href="#" class="icon-file-pdf" id="export_pdf">${_("PDF")}</a></li>
                                          <li><a href="#" class="icon-file-excel" id="export_csv">${_("CSV")}</a></li>
                                          <li><a href="#" class="icon-file-xml" id="export_xml">${_("XML")}</a></li>
                                        </ul>

                                    </div>
                                    </div>
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
        <td style="padding:15px 0px 15px 15px;"><span class="italic">${_("There are no abstracts submitted yet")}</span></td>
    </tr>
    % elif (filteredNumberAbstracts == "0"):
        <td style="padding:15px 0px 15px 15px;"><span class="italic">${_("There are no abstracts with the filters criteria selected")}</span></td>
    % else:
        <tr>
            <td></td>
        </tr>
        <tr>
            <td></td>
        % if "ID" in displayColumns:
           <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #888;"><a href="${getSortingURL('number')}"> ${_("ID")}</a>
                ${includeOrderImg("number")}
           </td>
        % endif
        <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"> ${_("Title")}</td>
        % if "PrimaryAuthor" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"> ${_("Primary Author(s)")}</td>
        % endif
        % if "Tracks" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href="${getSortingURL('track')}"> ${_("Tracks")}</a>
                ${includeOrderImg("track")}
           </td>
        % endif
        % if "Type" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href="${getSortingURL('type')}"> ${_("Type")}</a>
                ${includeOrderImg("type")}
           </td>
        % endif
        % if "Status" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href="${getSortingURL('status')}"> ${_("Status")}</a>
                ${includeOrderImg("status")}
           </td>
        % endif
        % if "Rating" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href="${getSortingURL('rating')}"> ${_("Rating")}</a>
                ${includeOrderImg("rating")}
           </td>
        % endif
        % if "AccTrack" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"> ${_("Acc. Track")}</td>
        % endif
        % if "AccType" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"> ${_("Acc. Type")}</td>
        % endif
        % if "SubmissionDate" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href="${getSortingURL('date')}"> ${_("Submission date")}</a>
                ${includeOrderImg("date")}
           </td>
        % endif
        % if "ModificationDate" in displayColumns:
            <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href="${getSortingURL('modifDate')}"> ${_("Modification date")}</a>
                ${includeOrderImg("modifDate")}
           </td>
        % endif
        </tr>
    % endif
    <tr><td>
        <tbody id="abstractsItems">
            % for abstract in abstracts:
                  <%include file="Abstract.tpl" args="abstract=abstract,display=displayColumns"/>
            % endfor
        </tbody>
    </td></tr>
</table>
</form>

<script type="text/javascript">
    var newAbst = false;

    function selectAllTracks() {
        $("#filterOptionForm #Tracks input:checkbox").prop("checked", true)
    }

    function unselectAllTracks() {
        $("#filterOptionForm #Tracks input:checkbox").prop("checked", false)
    }

    function selectAllTypes() {
        $("#filterOptionForm #Types input:checkbox").prop("checked", true)
    }

    function unselectAllTypes() {
        $("#filterOptionForm #Types input:checkbox").prop("checked", false)
    }

    function selectAllStatus() {
        $("#filterOptionForm #Status input:checkbox").prop("checked", true)
    };

    function unselectAllStatus() {
        $("#filterOptionForm #Status input:checkbox").prop("checked", false)
    }

    function selectAllAccTracks() {
        $("#filterOptionForm #AccTracks input:checkbox").prop("checked", true)
    }

    function unselectAllAccTracks() {
        $("#filterOptionForm #AccTracks input:checkbox").prop("checked", false)
    }

    function selectAllAccTypes() {
        $("#filterOptionForm #AccTypes input:checkbox").prop("checked", true)
    }

    function unselectAllAccTypes() {
        $("#filterOptionForm #AccTypes input:checkbox").prop("checked", false)
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
        $("tr[id^=abstracts] input:checkbox").on('change', function(){
            $(this).closest('tr').toggleClass('selected', this.checked);
        }).trigger('change');
    }

    function selectAll() {
        $('tr[id^=abstracts] input:checkbox').prop('checked', true).trigger('change');
    }

    function selectNone() {
        $('tr[id^=abstracts] input:checkbox').prop('checked', false).trigger('change');
    }


    $('#index_filter').click(
      function() {
        if ($("#displayMenu").is(":visible")) {
            $("#index_display").html($T("Select columns to display"));
            $('#index_display').addClass("CRLIndexUnselected").removeClass("CRLIndexSelected");
            $("#displayMenu").hide();
        }
        if ($("#filterMenu").is(":visible")) {
% if filterUsed:
            $("#index_filter").html($T("Show filters"));
% else:
            $("#index_filter").html($T("Apply filters"));
% endif
            $('#index_filter').addClass("CRLIndexUnselected").removeClass("CRLIndexSelected");
            $("#filterMenu").hide();
        }else { // the menu is hiden so, show it
            $("#index_filter").html($T("Hide filters"));
            $('#index_filter').removeClass("CRLIndexUnselected").addClass("CRLIndexSelected");
            $("#filterMenu").show();
        }
      });

    $('#index_display').click(
      function(){
        if ($("#filterMenu").is(":visible")) {
            % if filterUsed:
            $("#index_filter").html($T("Show filters"));
            % else:
            $("#index_filter").html($T("Apply filters"));
            % endif
            $('#index_filter').addClass("CRLIndexUnselected").removeClass("CRLIndexSelected");
            $("#filterMenu").hide();
        }
        if ($("#displayMenu").is(":visible")) {
            $("#index_display").html($T("Select columns to display"));
            $('#index_display').addClass("CRLIndexUnselected").removeClass("CRLIndexSelected");
            $("#displayMenu").hide();
        } else { // the menu is hiden so, show it
            $("#index_display").html($T("Close selection"));
            $('#index_display').removeClass("CRLIndexUnselected").addClass("CRLIndexSelected");
            $("#displayMenu").show();
        }
    });

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

$(function(){
    actionAbstractsRows();
    $('#button-menu').dropdown();

    $(window).scroll(function(){
        IndicoUI.Effect.followScroll();
    });

    // Cleanup previous actions
    var CleanupHiddenFields = function (){
        $("#abstractsForm input[type=hidden]").remove();
    };

    // Insert hidden field to the form
    var InsertHiddenField = function (name, array){
        for (var index in array){
            $('#abstractsForm').append($("<input>").attr("type", "hidden").attr("name", name).val(array[index]));
        }
    };

    _({
      "#accept_abstracts": {"acceptMultiple": [$T("Accept")]},
      "#reject_abstracts": {"rejectMultiple": [$T("Reject")]},
      "#merge_abstracts": {"merge": [$T("Merge")]},
      "#author_list": {"auth": [$T("Author List")]},
      "#download_attachments": {"PKGA": [$T("Download attachments")]},
      "#export_pdf": {"pdf": [$T("Export PDF")]},
      "#export_csv": {"excel": [$T("Export CSV")], "disp": ${displayColumns}},
      "#export_xml": {"xml": [$T("Export XML")]}
    }).each(function(vals, key) {
      $(key).bind('menu_select',function(){
        if (atLeastOneSelected()) {
            CleanupHiddenFields();
            for (var index in vals) {
                InsertHiddenField(index, vals[index]);
            }
            $('#abstractsForm').submit();
        }
      });
    });

    $("#add_new_abstract").bind('menu_select',function(){
      InsertHiddenField("newAbstract", [$T("Add")]);
      $('#abstractsForm').submit();
    });

    $("#selectDisplay").click(function(){
      $("#displayMenu input[type=checkbox]").prop("checked",true);
    });

    $("#unselectDisplay").click(function(){
      $("#displayMenu input[type=checkbox]").prop("checked",false);
    });

    $("#selectAll").click(function(){
      selectAll();
    });

    $("#selectNone").click(function(){
      selectNone();
    });
});

</script>
