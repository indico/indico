<script type="text/javascript">
<!--
    var newUser = false;

    function selectAcco()
    {
        document.filterOptionForm.accommShowNoValue.checked=true
        if (!document.filterOptionForm.accomm.length)
        {
            document.filterOptionForm.accomm.checked=true
        }else{
            for (i = 0; i < document.filterOptionForm.accomm.length; i++)
            {
                document.filterOptionForm.accomm[i].checked=true
            }
        }
    }

    function unselectAcco()
    {
        document.filterOptionForm.accommShowNoValue.checked=false
        if (!document.filterOptionForm.accomm.length)
        {
            document.filterOptionForm.accomm.checked=false
        }else{
            for (i = 0; i < document.filterOptionForm.accomm.length; i++)
            {
                document.filterOptionForm.accomm[i].checked=false
            }
        }
    }
    function selectEvent()
    {
        document.filterOptionForm.eventShowNoValue.checked=true
        if (!document.filterOptionForm.event.length)
        {
            document.filterOptionForm.event.checked=true
        }else{
            for (i = 0; i < document.filterOptionForm.event.length; i++)
            {
                document.filterOptionForm.event[i].checked=true
            }
        }
    }

    function unselectEvent()
    {
        document.filterOptionForm.eventShowNoValue.checked=false
        if (!document.filterOptionForm.event.length)
        {
            document.filterOptionForm.event.checked=false
        }else{
            for (i = 0; i < document.filterOptionForm.event.length; i++)
        	{
	            document.filterOptionForm.event[i].checked=false
    	    }
        }
    }
    function selectSession()
    {
        document.filterOptionForm.sessionShowNoValue.checked=true
        if (!document.filterOptionForm.session.length)
        {
            document.filterOptionForm.session.checked=true
        }else{
            for (i = 0; i < document.filterOptionForm.session.length; i++)
            {
                document.filterOptionForm.session[i].checked=true
            }
        }
    }

    function unselectSession()
    {
        document.filterOptionForm.sessionShowNoValue.checked=false
        if (!document.filterOptionForm.session.length)
        {
            document.filterOptionForm.session.checked=false
        }else{
            for (i = 0; i < document.filterOptionForm.session.length; i++)
            {
                document.filterOptionForm.session[i].checked=false;
            }
        }
    }

    function selectStatuses()
    {
        for (i = 0; i < document.filterOptionForm.statuses.length; i++)
        {
            document.filterOptionForm.statuses[i].checked=true;
        }
    }

    function selectOneStatus(elementName)
    {
        var inputNodes = IndicoUtil.findFormFields($E(elementName))
        for (i = 0; i < inputNodes.length; i++)
        {
            var node = formNodes[i];
            if (node.type == "checkbox") {
                node.checked = true;
            }
        }
    }

    function unselectOneStatus(elementName)
    {
        var inputNodes = IndicoUtil.findFormFields($E(elementName))
        for (i = 0; i < inputNodes.length; i++)
        {
            var node = formNodes[i];
            if (node.type == "checkbox") {
                node.checked = false;
            }
        }
    }

    function unselectStatuses()
    {
        for (i = 0; i < document.filterOptionForm.statuses.length; i++)
        {
            document.filterOptionForm.statuses[i].checked=false
        }
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

    window.onload = function(){
        isSelected("registrantsItems")
    }
//-->
</script>


<a href="" name="results"></a>
<table width="100%%" cellspacing="0" align="center" border="0">
        <tr>
           <td nowrap colspan="10">
                <div class="CRLgroupTitleNoBorder"><%= _("Displaying")%><strong> %(filteredNumberRegistrants)s </strong>
                <% if filteredNumberRegistrants == "1": %>
                    <%= _("registrant")%>
                <% end %>
                <% else: %>
                    <%= _("registrants")%>
                <% end %>
                <% if filterUsed: %>
                    (<%= _("Total")%>: <strong>%(totalNumberRegistrants)s</strong>)
                <% end %>
            </div>
            <form action=%(filterPostURL)s method="post" name="optionForm">
            <div class="CRLIndexList" >
                <% if filterUsed: %>
                    <input type="submit" class="btnRemove" name="resetFilters" value="Reset filters">
                    <span style="padding: 0px 6px 0px 6px">|</span>
                <% end %>
                <a id="index_filter" onclick="showFilters()" class="CAIndexUnselected" font-size="16" font-weight="bold" font-family="Verdana">
                  <% if filterUsed: %>
                    <%= _("Show filters")%>
                  <% end %>
                  <% else: %>
                    <%= _("Apply filters")%>
                  <% end %>
                </a>
                <span style="padding: 0px 6px 0px 6px">|</span>
                <a id="index_display" onclick="showDisplay()" class="CAIndexUnselected" font-size="16">
                    <%= _("Columns to display")%>
                </a>
            </div>
            </form>
            </td>
        </tr>
        <tr>
            <td colspan="10" align="left" width="100%%">
              <form action=%(filterPostURL)s method="post" name="displayOptionForm">
                <input type="hidden" name="operationType" value="display" />
                %(displayMenu)s
                %(sortingOptions)s
              </form>
              <form action=%(filterPostURL)s method="post" name="filterOptionForm">
                <input type="hidden" name="operationType" value="filter" />
                %(filterMenu)s
                %(sortingOptions)s
              </form>
            </td>
	   </tr>

        <tr>
          <td colspan="40" style="border-bottom:2px solid #777777;padding-top:5px" valign="bottom" align="left">
            <form action=%(actionPostURL)s method="post" name="registrantsForm" onSubmit="return atLeastOneSelected()">
	      <table>
                <tr>
                <tr>
                  <td colspan="10">
                    <div>
                      <input type="hidden" name="reglist" value="%(reglist)s">
                      %(displayOptions)s
                    </div>
                  </td>
                </tr>

                <td valign="bottom" align="left" class="eventModifButtonBar">
                  <input type="submit" class="btn" name="newRegistrant" onclick="newUser = true;" value="<%= _("Add New")%>">
                </td>
                <td valign="bottom" align="left">
                  <input type="submit" class="btn" name="removeRegistrants" value="<%= _("Remove")%>">
                </td>
                <td valign="bottom" align="left">
                  <input type="submit" class="btn" name="emailSelected" value="<%= _("Email")%>">
                </td>
                <td valign="bottom" align="left">
                  <input type="submit" class="btn" name="printBadgesSelected" value="<%= _("Print Badges")%>">
                </td>
                <td valign="bottom" align="left">
                  <input type="submit" class="btn" name="info.x" value="<%= _("Show Stats")%>">
                </td>
                <td valign="bottom" align="left">
                  Export to:
                </td>
                <td valign="bottom" align="left">
                  %(printIconURL)s
                </td>
                <td valign="bottom" align="left">
                  %(excelIconURL)s
                </td>
                </tr>
              </table>
          </td>
        </tr>
        <tr>
    %(columns)s
    <tbody id="registrantsItems">
    %(registrants)s
    </tbody>
    </tr>
        <tr>
        <td colspan="40" style="border-top: 2px solid #777777; padding-top: 3px;" valign="bottom" align="left">
            <table>
                <tbody>

                        <td valign="bottom" align="left" class="eventModifButtonBar">
                            <input type="submit" class="btn" name="newRegistrant" onclick="newUser = true;" value="<%= _("Add New")%>">
                        </td>
                        <td valign="bottom" align="left">
                            <input type="submit" class="btn" name="removeRegistrants" value="<%= _("Remove")%>">
                        </td>
                        <td valign="bottom" align="left">
                            <input type="submit" class="btn" name="emailSelected" value="<%= _("Email")%>">
                        </td>
                        <td valign="bottom" align="left">
                            <input type="submit" class="btn" name="printBadgesSelected" value="<%= _("Print Badges")%>">
                        </td>
                        <td valign="bottom" align="left">
                            <input type="submit" class="btn" name="info.x" value="<%= _("Show Stats")%>">
                        </td>
                        <td valign="bottom" align="left">
                            Export to:
                        </td>
                        <td valign="bottom" align="left">
                            %(printIconURL)s
                        </td>
                        <td valign="bottom" align="left">
                            %(excelIconURL)s
                        </td>

                </tbody>
            </table>
        </td>
    </tr>
</table>
</form>

<script type="text/javascript">
    function onMouseOver(element) {
        if ($E(element).dom.style.backgroundColor ==='transparent') {
           $E(element).dom.style.backgroundColor='rgb(255, 246, 223)';
        }
    }

    function onMouseOut(element) {
        var inputNodes = IndicoUtil.findFormFields($E(element))
        for (i = 0; i < inputNodes.length; i++) {
            var node = inputNodes[i];
            if (node.type == "checkbox") {
                if(node.checked !== true) {
                    $E(node.name+node.value).dom.style.backgroundColor='transparent';
                } else {
                    $E(node.name+node.value).dom.style.backgroundColor = "#CDEB8B";
                }
            }
        }
    }


    function atLeastOneSelected() {
        if(!newUser) {
            var inputNodes = IndicoUtil.findFormFields($E("registrantsItems"))
            for (i = 0; i < inputNodes.length; i++)
            {
                var node = formNodes[i];
                if (node.type == "checkbox") {
                    if(node.checked == true) {
                        return true;
                    }
                }
            }

            var dialog = new WarningPopup($T("Warning"), $T("No registrant selected! Please select at least one."));
            dialog.open();

            return false;
        } else {
            return true;
        }
    }

    function isSelected(element) {
        var inputNodes = IndicoUtil.findFormFields($E(element))
        for (i = 0; i < inputNodes.length; i++) {
            var node = inputNodes[i];
            if (node.type == "checkbox") {
                if(node.checked == true) {
                    $E(node.name+node.value).dom.style.backgroundColor = "#CDEB8B";
                } else {
                    $E(node.name+node.value).dom.style.backgroundColor='transparent';
                }
            }
        }
    }

    function showFilters() {
        if ($E("displayMenu").dom.style.display == "") {
            $E("index_display").set('<%= _("Select columns to display")%>');
            $E('index_display').dom.className = "CRLIndexUnselected";
            $E("displayMenu").dom.style.display = "none";
        }
        if ($E("filterMenu").dom.style.display == "") {
<% if filterUsed: %>
            $E("index_filter").set('<%= _("Show filters")%>');
<% end %>
<% else: %>
            $E("index_filter").set('<%= _("Apply filters")%>');
<% end %>
            $E('index_filter').dom.className = "CRLIndexUnselected";
            $E("filterMenu").dom.style.display = "none";
        }else {
            $E("index_filter").set('<%= _("Hide filters")%>');
            $E('index_filter').dom.className = "CRLIndexSelected";
            $E("filterMenu").dom.style.display = "";
        }
    }
    function showDisplay() {
        if ($E("filterMenu").dom.style.display == "") {
<% if filterUsed: %>
            $E("index_filter").set('<%= _("Show filters")%>')
<% end %>
<% else: %>
            $E("index_filter").set('<%= _("Apply filters")%>');
<% end %>
           $E('index_filter').dom.className = "CRLIndexUnselected";
            $E("filterMenu").dom.style.display = "none";
        }
        if ($E("displayMenu").dom.style.display == "") {
            $E("index_display").set('<%= _("Select columns to display")%>');
            $E('index_display').dom.className = "CRLIndexUnselected";
            $E("displayMenu").dom.style.display = "none";
        }else {
            $E("index_display").set('<%= _("Close selection")%>');
            $E('index_display').dom.className = "CRLIndexSelected";
            $E("displayMenu").dom.style.display = "";
        }
    }
</script>
