<div class="container" style="max-width: 1000px; overflow: visible;">
<form id="eventCreationForm" action="<%= postURL %>" method="POST">

    <input type="hidden" name="event_type" value="<%= event_type %>">

    <em><%= _("Please follow the steps to create a lecture")%></em>
    <div class="groupTitle"><%= _("Step 1: Choose a category")%></div>
    <div style="padding: 10px">
        <input type="hidden" value="<%= categ['id'] %>" name="categId" id="createCategId"/>
        <span class="selectedCategoryName"><%= _("The event will be created in:")%> <span id="categTitle" class="categTitleChosen"><%= categ['title'] %></span></span><input <% if nocategs: %>style="display: none;"<% end %> id="buttonCategChooser" type="button" value="<%= _("Browse...")%>" onclick="openCategoryChooser()"/>
    </div>

    <div class="groupTitle"><%= _("Step 2: Enter basic information about the lecture") %></div>

    <table class="groupTable">
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Title")%></span></td>
            <td nowrap class="contentCellTD">
                    <input type="text" name="title" size="80" value="<%= title %>">
            </td>
        </tr>
        <!-- <Date and time> -->
        <tr>
            <td rowspan="2" nowrap class="titleCellTD"><span class="titleCellFormat">Dates</span><br></td>
            <td class="contentCellTD">
                <%= _("The lecture will take place in")%>
                <select id="nbDates"  name="nbDates" onChange="javascript:nbDatesChanged();">
                    <option value="1"> 1 </option>
                    <option value="2"> 2 </option>
                    <option value="3"> 3 </option>
                    <option value="4"> 4 </option>
                    <option value="5"> 5 </option>
                    <option value="6"> 6 </option>
                    <option value="7"> 7 </option>
                    <option value="8"> 8 </option>
                    <option value="9"> 9 </option>
                </select>
                <%= _("date(s)")%>
            </td>
        </tr>
        <tr>
            <td class="contentCellTD">
                <div id="datesContainer">
                    <!-- Filled through DOM manipulation   -->
                </div>
            </td>
        </tr>
        <!-- </Date and time> -->
        <!-- Fermi timezone awareness -->
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Timezone")%></span></td>
            <td class="contentCellTD">
                <select name="Timezone">%(timezoneOptions)s</select>
            </td>
        </tr>
        <% includeTpl('EventLocationInfo', modifying=False, showParent=False) %>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Speaker") %></span>
            </td>
            <td class="contentCellTD">
                <input type="hidden" id="chairperson" name="chairperson" value="">
                <div id="chairpersonsContainer">
                <!-- Filled through DOM manipulation   -->
                </div>
            </td>
        </tr>
        <tr>
            <td>&nbsp;</td>
            <td class="contentCellTD" style="font-style: italic; padding-top: 10px;"><span id="advancedOptionsText" class="fakeLink" onclick="showAdvancedOptions()">&nbsp;</span></td>
        </tr>

        <tr id="advancedOptions" style="display:none"><td colspan="2">

                <table class="groupTable">
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Description")%></span></td>
                        <td nowrap id="descriptionBox" class="contentCellTD">
                        </td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Default layout style")%></span></td>
                        <td class="contentCellTD">
                            <select name="defaultStyle"><%= styleOptions %></select>
                        </td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Keywords")%><br><small>(<%= _("one per line")%>)</small></span></td>
                        <td nowrap class="contentCellTD">
                            <textarea name="keywords" cols="60" rows="3"><%= keywords %></textarea>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <% includeTpl('EventSetProtection', eventType='lecture') %>

    <table class="groupTable" style="background-color: #ECECEC; border-top: 1px dashed #777777;">
        <tr>
            <td width="15%%" nowrap>&nbsp;</td>
            <td nowrap  style="padding: 10px 0;">
                <input style="font-weight: bold;" type="submit" name="ok" value="<%= _("Create lecture")%>">
            </td>
        </tr>
    </table>

</form>

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

    var uf = new UserListField('VeryShortPeopleListDiv', 'PeopleList',
            null, true, null,
            true, false, false, {"grant-manager": ['<%= _("event modification")%>', false]},
            true, false, true,
            userListNothing, userListNothing, userListNothing);

    $E('chairpersonsContainer').set(uf.draw());


    // ----- Categ Chooser
    var categoryChooserHandler = function(categ, protection){
        $E("createCategId").set(categ.id);
        $E("categTitle").set(categ.title);
        $E("buttonCategChooser").set("<%= _("Change...")%>")
        IndicoUI.Effect.highLightBackground("categTitle");

        updateProtectionChooser(categ.title, protection);
    };

    var openCategoryChooser = function() {
        var categoryChooserPopup = new CategoryChooser(<%= categ %>, categoryChooserHandler, true);
        categoryChooserPopup.open();
    }

    // ---- On Load

	IndicoUI.executeOnLoad(function()
	{

        nbDatesChanged();

        showAdvancedOptions();

        if ("<%=categ["id"]%>" != ""){
            $E("buttonCategChooser").set("<%= _("Change...")%>");
        }

        protectionChooserExecOnLoad("<%=categ["id"]%>", "<%=protection%>");

		injectValuesInForm($E('eventCreationForm'),function() {
                if (!verifyDates()) {
                    var popup = new ErrorPopup("Invalid dates", ["<%= _("Dates have an invalid format: dd/mm/yyyy hh:mm")%>"], "");
                    popup.open();
                    return false
                }
                if ($E("createCategId").get() == "") {
                    var popup = new ErrorPopup("<%= _("Missing mandatory data")%>", ["<%= _("Please, choose a category (step 1)")%>"], "");
                    popup.open();
                    return false;
                }else {
                    $E('chairperson').set(Json.write(uf.getUsers()));
                    injectFromProtectionChooser();
                }
        });

        verifyDates();


	var editor = new RichTextWidget(500, 200, {name: 'description'});
	$E('descriptionBox').set(editor.draw());


	});


</script>
