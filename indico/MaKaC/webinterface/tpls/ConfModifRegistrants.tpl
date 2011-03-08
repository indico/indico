<script type="text/javascript">
<!--
    var newUser = false;

    <%include file="ListJSHelpers.tpl"/>

    window.onload = function(){
        isSelected("registrantsItems")
    }

    function selectDisplay()
    {
        for (i = 0; i < document.displayOptionForm.disp.length; i++)
        {
            document.displayOptionForm.disp[i].checked=true
        }
    }

    function unselectDisplay()
    {
        for (i = 0; i < document.displayOptionForm.disp.length; i++)
        {
            document.displayOptionForm.disp[i].checked=false
        }
    }

    function selectAll()
    {
        if (!document.registrantsForm.registrant.length)
        {
            document.registrantsForm.registrant.checked=true
        }else{
            for (i = 0; i < document.registrantsForm.registrant.length; i++)
            {
                document.registrantsForm.registrant[i].checked=true;
            }
        }
        isSelected("registrantsItems")
    }

    function deselectAll()
    {
        if (!document.registrantsForm.registrant.length)
        {
            document.registrantsForm.registrant.checked=false
        }else{
            for (i = 0; i < document.registrantsForm.registrant.length; i++)
            {
                document.registrantsForm.registrant[i].checked=false;
            }
        }
        isSelected("registrantsItems")
    }

//-->
</script>


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
        <tr>
            <td colspan="1000" align="left" width="100%">
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
            <td colspan="1000" align="left" width="100%">
                <input type="text" id="staticURL" size="74" style="display: none;" readonly="readonly" value="${ filterUrl }" />
                <a id="staticURLLink" style="display: none; margin-left: 5px;" href="${ filterUrl }">${ _("Go to URL")}</a>
            </td>
        </tr>

        <tr>
          <td colspan="40" style="border-bottom:2px solid #777777;padding-top:5px" valign="bottom" align="left">
            <form action=${ actionPostURL } method="post" name="registrantsForm" onsubmit="return atLeastOneSelected($E('registrantsItems'), $T('No registrant selected! Please select at least one.'));">
          <table>
                <tr>
                  <td colspan="10">
                    <div>
                      <input type="hidden" name="reglist" value="${ reglist }">
                      ${ displayOptions }
                    </div>
                  </td>
                </tr>

                <tr>
                <td valign="bottom" align="left" class="eventModifButtonBar">
                  <input type="submit" class="btn" name="newRegistrant" onclick="newUser = true;" value="${ _("Add new")}">
                </td>
                <td valign="bottom" align="left">
                  <input type="submit" class="btn" name="removeRegistrants" value="${ _("Remove")}">
                </td>
                <td valign="bottom" align="left">
                  <input type="submit" class="btn" name="emailSelected" value="${ _("Email")}">
                </td>
                <td valign="bottom" align="left">
                  <input type="submit" class="btn" name="printBadgesSelected" value="${ _("Print badges")}">
                </td>
                <td valign="bottom" align="left">
                  <input type="submit" class="btn" name="info.x" value="${ _("Show stats")}">
                </td>
                <td valign="bottom" align="left">
                  Export to:
                </td>
                <td valign="bottom" align="left">
                  ${ printIconURL }
                </td>
                <td valign="bottom" align="left">
                  ${ excelIconURL }
                </td>
                </tr>
              </table>
          </td>
        </tr>
        <tr>
    ${ columns }
    <tbody id="registrantsItems">
    ${ registrants }
    </tbody>
    </tr>
        <tr>
        <td colspan="40" style="border-top: 2px solid #777777; padding-top: 3px;" valign="bottom" align="left">
            <table>
                <tbody>

                        <td valign="bottom" align="left" class="eventModifButtonBar">
                            <input type="submit" class="btn" name="newRegistrant" onclick="newUser = true;" value="${ _("Add new")}">
                        </td>
                        <td valign="bottom" align="left">
                            <input type="submit" class="btn" name="removeRegistrants" value="${ _("Remove")}">
                        </td>
                        <td valign="bottom" align="left">
                            <input type="submit" class="btn" name="emailSelected" value="${ _("Email")}">
                        </td>
                        <td valign="bottom" align="left">
                            <input type="submit" class="btn" name="printBadgesSelected" value="${ _("Print badges")}">
                        </td>
                        <td valign="bottom" align="left">
                            <input type="submit" class="btn" name="info.x" value="${ _("Show stats")}">
                        </td>
                        <td valign="bottom" align="left">
                            Export to:
                        </td>
                        <td valign="bottom" align="left">
                            ${ printIconURL }
                        </td>
                        <td valign="bottom" align="left">
                            ${ excelIconURL }
                        </td>

                </tbody>
            </table>
        </td>
    </tr>
</table>
</form>

<script type="text/javascript">

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
            $E("index_filter").set('${ _("Show filters")}')
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
</script>