<script type="text/javascript">
<!--
    var newUser = false;

    function selectAcco()
    {
        document.optionForm.accommShowNoValue.checked=true
        if (!document.optionForm.accomm.length)
        {
            document.optionForm.accomm.checked=true
        }else{
            for (i = 0; i < document.optionForm.accomm.length; i++)
            {
                document.optionForm.accomm[i].checked=true
            }
        }
    }

    function unselectAcco()
    {
        document.optionForm.accommShowNoValue.checked=false
        if (!document.optionForm.accomm.length)
        {
            document.optionForm.accomm.checked=false
        }else{
            for (i = 0; i < document.optionForm.accomm.length; i++)
            {
                document.optionForm.accomm[i].checked=false
            }
        }
    }
    function selectEvent()
    {
        document.optionForm.eventShowNoValue.checked=true
        if (!document.optionForm.event.length)
        {
            document.optionForm.event.checked=true
        }else{
            for (i = 0; i < document.optionForm.event.length; i++)
            {
                document.optionForm.event[i].checked=true
            }
        }
    }

    function unselectEvent()
    {
        document.optionForm.eventShowNoValue.checked=false
        if (!document.optionForm.event.length)
        {
            document.optionForm.event.checked=false
        }else{
            for (i = 0; i < document.optionForm.event.length; i++)
        	{
	            document.optionForm.event[i].checked=false
    	    }
        }
    }
    function selectSession()
    {
        document.optionForm.sessionShowNoValue.checked=true
        if (!document.optionForm.session.length)
        {
            document.optionForm.session.checked=true
        }else{
            for (i = 0; i < document.optionForm.session.length; i++)
            {
                document.optionForm.session[i].checked=true
            }
        }
    }

    function unselectSession()
    {
        document.optionForm.sessionShowNoValue.checked=false
        if (!document.optionForm.session.length)
        {
            document.optionForm.session.checked=false
        }else{
            for (i = 0; i < document.optionForm.session.length; i++)
            {
                document.optionForm.session[i].checked=false;
            }
        }
    }

    function selectStatuses()
    {
        for (i = 0; i < document.optionForm.statuses.length; i++)
        {
            document.optionForm.statuses[i].checked=true;
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
        for (i = 0; i < document.optionForm.statuses.length; i++)
        {
            document.optionForm.statuses[i].checked=false
        }
    }

    function selectDisplay()
    {
        for (i = 0; i < document.optionForm.disp.length; i++)
        {
        	document.optionForm.disp[i].checked=true
    	}
    }

    function unselectDisplay()
    {
        for (i = 0; i < document.optionForm.disp.length; i++)
    	{
	        document.optionForm.disp[i].checked=false
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
            </td>
        </tr>
        <tr>
            <td colspan="10" align="left" width="100%%">
              <form action=%(filterPostURL)s method="post" name="optionForm">
                <input type="hidden" name="operationType" value="display" />
                %(displayMenu)s
                %(sortingOptions)s
              </form>
              <form action=%(filterPostURL)s method="post" name="optionForm">
                <input type="hidden" name="operationType" value="filter" />
                %(filterMenu)s
                %(sortingOptions)s
              </form>
            </td>
	   </tr>
        <tr>
            <td colspan="10">
                <div>
                    <input type="hidden" name="reglist" value="%(reglist)s">
                        %(displayOptions)s
                </div>
            </td>
        </tr>


    <tr>
        <td colspan="40" style="border-bottom:2px solid #777777;padding-top:5px" valign="bottom" align="left">
		    <table>
             <form action=%(actionPostURL)s method="post" name="registrantsForm" onSubmit="return atLeastOneSelected()">

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
