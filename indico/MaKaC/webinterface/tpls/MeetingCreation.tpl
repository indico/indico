<div class="container" style="max-width: 1000px; overflow: visible;">
<form id="eventCreationForm" action="<%= postURL %>"  method="POST">
    <input type="hidden" name="event_type" value="<%= event_type %>">
    <input type="hidden" name="sessionSlots" value="disabled"/>

    <em><%= _("Please follow the steps to create a meeting")%></em>

    <div class="groupTitle"><%= _("Step 1: Choose a category")%></div>

    <div style="padding: 10px">
        <input type="hidden" value="<%= categ['id'] %>" name="categId" id="createCategId"/>
        <span class="selectedCategoryName"><%= _("The event will be created in:")%> <span id="categTitle" class="categTitleChosen"><%= categ['title'] %></span></span><input <% if nocategs: %>style="display: none;"<% end %> id="buttonCategChooser" type="button" value="<%= _("Browse...")%>" onclick="openCategoryChooser()"/>
    </div>

	<div class="groupTitle"><%= _("Step 2: Enter basic information about the meeting") %></div>

    <table class="groupTable">
	    <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Title")%></span></td>
            <td nowrap class="contentCellTD">
                    <input type="text" name="title" size="80" value="<%= title %>">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Start date")%></span></td>
            <td class="contentCellTD">
				<span id="sDatePlace"></span>
				<input type="hidden" value="" name="sDay" id="sDay"/>
				<input type="hidden" value="" name="sMonth" id="sMonth"/>
				<input type="hidden" value="" name="sYear" id="sYear"/>
                <input type="hidden" name="sHour" id="sHour" value=""/>
                <input type="hidden" name="sMinute" id="sMinute" value=""/>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("End date")%></span></td>
            <td class="contentCellTD">
				<span id="eDatePlace"></span>
				<input type="hidden" value="" name="eDay" id="eDay"/>
				<input type="hidden" value="" name="eMonth" id="eMonth"/>
				<input type="hidden" value="" name="eYear" id="eYear"/>
                <input type="hidden" id="eHour" name="eHour" value="">
                <input type="hidden" id="eMinute" name="eMinute" value="">
				<span><a href="#" onclick="new ShowConcurrentEvents(createDatesDict()).execute()"><%= _("Show existing events during these dates")%></a></span>
            </td>
        </tr>
        <!-- Fermi timezone awareness -->
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Timezone")%></span></td>
            <td class="contentCellTD">
                <select id="Timezone" name="Timezone"><%= timezoneOptions %></select>
            </td>
        </tr>
        <!-- Fermi timezone awareness(end) -->

    	<% includeTpl('EventLocationInfo', modifying=False, showParent=False) %>

        <tr>
            <td>&nbsp;</td>
            <td class="contentCellTD" style="font-style: italic; padding-top: 10px;"><span id="advancedOptionsText" class="fakeLink" onclick="showAdvancedOptions()">&nbsp;</span></td>
        </tr>

        <tr id="advancedOptions" style="display:none"><td colspan="2">

            <table class="groupTable">
            <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Description")%></span></td>
            <td nowrap  class="contentCellTD" id="descriptionBox">
            </td>
            </tr>
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Default layout style")%></span></td>
                <td  class="contentCellTD">
                    <select name="defaultStyle"><%= styleOptions %></select>
            </td>
            </tr>

            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Chairperson") %></span></td>
                <td class="contentCellTD">
                    <input type="hidden" id="chairperson" name="chairperson" value="">
                    <div id="chairpersonsContainer">
                    <!-- Filled through DOM manipulation   -->
                    </div>
                </td>
            </tr>
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Keywords")%><br><small>(<%= _("one per line")%>)</small></span></td>
                <td nowrap class="contentCellTD">
                    <textarea name="keywords" cols="60" rows="3"><%= keywords %></textarea>
                </td>
            </tr>
            </table>
        </td></tr>
    </table>
    <table class="groupTable" style="background-color: #ECECEC; border-top: 1px dashed #777777;">
        <tr>
            <td width="15%%" nowrap>&nbsp;</td>
            <td nowrap  style="padding: 10px 0;">
                <input style="font-weight: bold;" type="submit" name="ok" value="<%= _("Create meeting")%>">
            </td>
        </tr>
    </table>


</form>
</div>
<% includeTpl('EventCreationJS') %>

<script  type="text/javascript">
    var advOptSwitch = true;
    function showAdvancedOptions() {
        if (advOptSwitch) {
            $E("advancedOptions").dom.style.display = "none";
            $E("advancedOptionsText").set('<%= _("Show advanced options...")%>');
        }else {
            $E("advancedOptions").dom.style.display = "";
            $E("advancedOptionsText").set('<%= _("Hide advanced options...")%>');
        }
        advOptSwitch = !advOptSwitch;
    }

    //---- chairperson management

    var userList = [];
    <% from MaKaC.common.PickleJar import DictPickler %>
    var uf = new UserListField('VeryShortPeopleListDiv', 'PluginPeopleList',
            userList,
		    null,
		    <%= jsonEncode(DictPickler.pickle(rh._getUser().getPersonalInfo().getBasket().getUsers())) %>,
		    true, true, false,
		    userListNothing, userListNothing, userListNothing, false,
            {"grant-manager": ['<%= _("event modification")%>', false]});

    $E('chairpersonsContainer').set(uf.draw());

    // ----- show concurrent events
    function createDatesDict() {
        if (verifyDates()) {

            var res = {};

            res["sDate"] = Util.formatDateTime(dates.item(0).get(), IndicoDateTimeFormats.Server, IndicoDateTimeFormats.Default);
            res["eDate"] = Util.formatDateTime(dates.item(1).get(), IndicoDateTimeFormats.Server, IndicoDateTimeFormats.Default);
            res["timezone"] = $E('Timezone').get();

            return res;
        }else{
            var popup = new ErrorPopup('<%= _("Invalid dates")%>', ["<%= _("Dates have an invalid format: dd/mm/yyyy hh:mm")%>"], "");
            popup.open();
            return null;
        }

    }

    // ----- Categ Chooser
    var categoryChooserHandler = function(categ){
        $E("createCategId").set(categ.id);
        $E("categTitle").set(categ.title);
        $E("buttonCategChooser").set("<%= _("Change...")%>")
        IndicoUI.Effect.highLightBackground("categTitle");
    };

    var openCategoryChooser = function() {
        var categoryChooserPopup = new CategoryChooser(<%= categ %>, categoryChooserHandler, true);
        categoryChooserPopup.open();
    }

    // ---- On Load
    IndicoUI.executeOnLoad(function()
	{
        showAdvancedOptions();

        if ("<%=categ["id"]%>" != ""){
            $E("buttonCategChooser").set("<%= _("Change...")%>");
        }

		var startDate = IndicoUI.Widgets.Generic.dateField(true,null,['sDay', 'sMonth', 'sYear','sHour', 'sMinute']);
		$E('sDatePlace').set(startDate);

		var endDate = IndicoUI.Widgets.Generic.dateField(true,null,['eDay', 'eMonth', 'eYear', 'eHour', 'eMinute']);
		$E('eDatePlace').set(endDate);

		<% if sDay != '': %>
			startDate.set('<%= sDay %>/<%= sMonth %>/<%= sYear %><%= " " %><%= sHour %>:<%= sMinute %>');
		<% end %>

		<% if eDay != '': %>
			endDate.set('<%= eDay %>/<%= eMonth %>/<%= eYear %><%= " " %><%= eHour %>:<%= eMinute %>');
		<% end %>

		dates.append(startDate);
		dates.append(endDate);

        injectValuesInForm($E('eventCreationForm'),function() {
                if (!verifyDates()) {
                    var popup = new ErrorPopup('<%= _("Invalid dates")%>', ["<%= _("Dates have an invalid format: dd/mm/yyyy hh:mm")%>"], "");
                    popup.open();
                    return false
                }
                if ($E("createCategId").get() == "") {
                    var popup = new ErrorPopup("<%= _("Missing mandatory data")%>", ["<%= _("Please, choose a category (step 1)")%>"], "");
                    popup.open();
                    return false;
                }else {
                    $E('chairperson').set(Json.write(uf.getUsers()));
                }
        });

	verifyDates();

	var editor = new RichTextWidget(500, 200, {name: 'description'});
	$E('descriptionBox').set(editor.draw());
	});

</script>
