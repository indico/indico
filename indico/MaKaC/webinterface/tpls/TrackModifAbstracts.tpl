<table width="95%" align="left" valign="top" cellspacing="0">
    <tr>
        <td>
            <table width="100%">
                <tr>
                    <td>
                        <table bgcolor="white" width="100%">
                            <tr>
                                <form action=${ accessAbstract } method="post">
                                <td class="titleCellFormat"> ${ _("Quick search: Abstract ID")} = <input type="text" name="abstractId" size="4"><input type="submit" class="btn" value="${ _("seek it")}"><br>
                                </td>
                                </form>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td class="CRLgroupTitleNoBorder">${ _("Displaying")}<strong> ${ filteredNumberAbstracts } </strong>
                    % if filteredNumberAbstracts == "1":
                        ${ _("abstract")}
                    % else:
                        ${ _("abstracts")}
                    % endif
                    % if filterUsed:
                        (${ _("Total")}: <strong>${ totalNumberAbstracts }</strong>)
                    % endif
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td width="100%">
            % if filterUsed:
                <span id="resetLink" class="btnRemove" onclick="window.location = '${ resetFiltersURL }';" style="padding-left:6px;">${ _("Reset filters") }</span>
                <span style="padding: 0px 6px 0px 0px">|</span>
            % endif
            <span id="filtersLink" class="CRLIndexUnselected" onclick="showFilters();" style="cursor:pointer; padding-left:6px;">${ _("Show filters") if (filterUsed) else _("Apply filters") }</span>
        </td>
    </tr>
    <tr>
        <td>
            <div id="filters" style="display:none" class="CRLDiv">
                <form action=${ filterPostURL } method="POST">
                    ${ currentSorting }
                    <table width="100%" border="0">
                        <tr>
                            <td>
                                <table width="100%">
                                    <tr>
                                        <td>
                                            <table align="center" cellspacing="10" width="100%">
                                                <tr>
                                                    <td align="left" class="titleCellFormat" style="border-bottom: 1px solid #888888;"> ${ _("show contribution types")}</td>
                                                    <td align="left" class="titleCellFormat" style="border-bottom: 1px solid #888888;"> ${ _("show in status")}</td>
                                                    <td align="left" class="titleCellFormat" style="border-bottom: 1px solid #888888;"> ${ _("show acc. contribution types")}</td>
                                                    <td align="left" class="titleCellFormat" style="border-bottom: 1px solid #888888;"> ${ _("others")}</td>
                                                </tr>
                                                <tr>
                                                    <td valign="top">${ types }</td>
                                                    <td valign="top">${ status }</td>
                                                    <td valign="top">${ accTypes }</td>
                                                    <td valign="top">${ others }</td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td align="center" style="padding:10px"><input type="submit" class="btn" name="OK" value="${ _("Apply filter")}"></td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </form>
            </div>
        </td>
    </tr>
    <tr>
        <td>
            <a name="abstracts"></a>
            <table width="100%" cellspacing="0" border="0" style="padding-left:2px">
                <tr>
                    <td colspan="7" style="border-bottom: 2px solid #777777; padding-bottom: 3px;" valign="bottom" align="left">
                      % if canModify:
                          <a href="${ allAbstractsURL }" style="float:right; margin-top: 15px;">${ _("Go to all abstracts")}</a>
                      % endif

                        <table>
                            <tr>
                                <form action=${ actionURL } method="post" name="abstractsForm" target="_blank" onSubmit="return atLeastOneSelected();">
                                <td nowrap><input type="submit" class="btn" name="PART" value="${ _("Participant list")}"></td>
                                <td valign="bottom" align="left" nowrap>${ _("Export to:") }</td>
                                <td valign="bottom" align="left" nowrap>
                                    <input type="image" id="PDF" name="PDF" src=${ pdfIconURL} border="0" value="${ _("PDF of selected")}">
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
                    <td colspan="7" style="padding: 5px 0px 10px;" nowrap>${ _("Select: ") }<a style="color: #0B63A5;" id="selectAll">${ _("All") }</a>, <a style="color: #0B63A5;" id="deselectAll">${ _("None") }</a></td>
                </tr>
                <tr>
                    <td></td>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #888;"><a href="${ numberSortingURL }"> ${_("ID")}</a> ${ numberImg }</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF">${ _("Title")}</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href="${ typeSortingURL }">${ _("Type")}</a> ${ typeImg }</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href="${ statusSortingURL }">${ _("Status")}</a><b> ${ statusImg }</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"> ${ _("Acc. Type")}</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF"><a href="${ dateSortingURL }"> ${ _("Submission date")}</a> ${ dateImg }</td>
                </tr>
                 % endif
                <form action=${ actionURL } method="post" name="abstractsForm" target="_blank" onSubmit="return atLeastOneSelected()">
                <tbody id="abstractsItems">
                    ${ abstracts }
                </tbody>
                <tr>
                    <td colspan="7" style="border-top:2px solid #777777;" valign="bottom" align="left">
                        <table align="left">
                            <tr>
                                <td nowrap valign="bottom" align="left">
                                    <input type="submit" class="btn" name="PART" value="${ _("Participant list")}">
                                </td>
                                <td nowrap valign="bottom" align="left">${ _("Export to:") }</td>
                                <td nowrap valign="bottom" align="left">
                                    <input type="image" name="PDF" src=${ pdfIconURL} border="0" value="${ _("PDF of selected")}">
                                </td>

                                </form>
                                </form>
                            </tr>
                        </table>
                        % if canModify:
                          <a href="${ allAbstractsURL }" style="float:right;">${ _("Go to all abstracts")}</a>
                        % endif
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<script>

function showFilters() {
    if ($E('filters').dom.style.display == 'none') {
        $E('filters').dom.style.display = '';
        $E('filtersLink').set($T('Hide filters'));
        $E('filtersLink').dom.className = "CRLIndexSelected";
    } else {
        $E('filters').dom.style.display = 'none';
        % if filterUsed:
            $E('filtersLink').set($T('Show filters'));
        % else:
            $E('filtersLink').set($T('Apply filters'));
        % endif
        $E('filtersLink').dom.className = "CRLIndexUnselected";
    }
}


$(function() {
    $('.abstract input').change(function() {
        if (this.checked) {
            $(this).parents('.abstract').addClass('selected');
        } else {
            $(this).parents('.abstract').removeClass('selected');
        }
    });

    $('#selectAll').click(function() {
        $('.abstract input:not(:disabled)').prop('checked', true)
        $('.abstract input').trigger('change');
    });

    $('#deselectAll').click(function() {
        $('.abstract input:not(:disabled)').prop('checked', false)
        $('.abstract input').trigger('change');
    });

});

function atLeastOneSelected() {
    if($('.abstract input:not(:disabled):checked').length) {
        return true;
    } else {
        var dialog = new WarningPopup($T("Warning"), $T("No abstract selected! Please select at least one."));
        dialog.open();
        return false;
    }
}

</script>
