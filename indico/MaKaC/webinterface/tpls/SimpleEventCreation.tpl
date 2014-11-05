<div class="container" style="max-width: 1000px; overflow: visible;">
<form id="eventCreationForm" action="${ postURL }" method="POST">

    <input type="hidden" name="event_type" value="${ event_type }">

    <em>${ _("Please follow the steps to create a lecture")}</em>
    <div class="groupTitle">${ _("Step 1: Choose a category")}</div>
    <div style="padding: 10px">
        <input type="hidden" value="${ categ['id'] }" name="categId" id="createCategId"/>
        <span class="selectedCategoryName">${ _("The event will be created in:")} <span id="categTitle" class="categTitleChosen">${ categ['title'] }</span></span><input ${'style="display: none;"' if nocategs else ""} id="buttonCategChooser" type="button" value="${ _("Browse...")}" onclick="openCategoryChooser()"/>
    </div>

    <div class="groupTitle">${ _("Step 2: Enter basic information about the lecture") }</div>

    <table class="groupTable">
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Title")}</span></td>
            <td nowrap class="contentCellTD">
                    <input type="text" name="title" size="80" value="${ title }">
            </td>
        </tr>
        <!-- <Date and time> -->
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Date(s)")}</span><br></td>
            <td class="contentCellTD">
                <div id="datesContainer">
                    <!-- Filled through DOM manipulation   -->
                </div>
                <input type="hidden" id="nbDates" name="nbDates" value="1">
            </td>
        </tr>
        <!-- </Date and time> -->
        <!-- Fermi timezone awareness -->
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Timezone")}</span></td>
            <td class="contentCellTD">
                <select name="Timezone">${ timezoneOptions }</select>
            </td>
        </tr>
        <%include file="EventLocationInfo.tpl" args="modifying=False, showParent=False, conf=False"/>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat">${ _("Speaker") }</span>
            </td>
            <%include file="EventParticipantAddition.tpl"/>
        </tr>
        <tr>
            <td>&nbsp;</td>
            <td class="contentCellTD" style="font-style: italic; padding-top: 10px;"><span id="advancedOptionsText" class="fakeLink">&nbsp;</span></td>
        </tr>

        <tr id="advancedOptions" style="display:none"><td colspan="2">

                <table class="groupTable">
                    <tr>
                        <td nowrap class="titleCellTD">
                            <span class="titleCellFormat"> ${ _("Description")}</span>
                            <input type="hidden" id="description" name="description" value="">
                        </td>
                        <td nowrap id="descriptionBox" class="contentCellTD">
                        </td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Default layout style")}</span></td>
                        <td class="contentCellTD">
                            <select name="defaultStyle">${ styleOptions }</select>
                        </td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Keywords")}<br><small>(${ _("one per line")})</small></span></td>
                        <td nowrap class="contentCellTD">
                            <textarea name="keywords" cols="60" rows="3">${ keywords }</textarea>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <%include file="EventSetProtection.tpl" args="eventType='lecture'"/>

    <table class="groupTable" style="background-color: #ECECEC; border-top: 1px dashed #777777;">
        <tr>
            <td width="15%" nowrap>&nbsp;</td>
            <td nowrap  style="padding: 10px 0;">
                <input style="font-weight: bold;" type="submit" name="ok" value="${ _("Create lecture")}">
            </td>
        </tr>
    </table>

</form>

<%include file="EventCreationJS.tpl"/>

<script  type="text/javascript">

    // ----- Categ Chooser
    var categoryChooserHandler = function(categ, protection){
        $E("createCategId").set(categ.id);
        $E("categTitle").set(categ.title);
        $E("buttonCategChooser").set("${ _("Change...")}")
        IndicoUI.Effect.highLightBackground($E("categTitle"));

        updateProtectionChooser(categ.title, protection);
    };

    var openCategoryChooser = function() {
        var categoryChooserPopup = new CategoryChooser(${ categ | n,j}, categoryChooserHandler, true);
        categoryChooserPopup.open();
    }

    // ---- On Load

    IndicoUI.executeOnLoad(function()
    {

        initializeDatesContainer();

        showAdvancedOptions();

        if ("${categ["id"]}" != ""){
            $E("buttonCategChooser").set($T('Change...'));
        }

        protectionChooserExecOnLoad("${categ["id"]}", "${protection}");

        injectValuesInForm($E('eventCreationForm'),function() {
                if (verifyLectureDates()) {
                    if (showLectureDatesStorageErrorPopup()) {
                        return false;
                    }
                } else {
                    var popup = new ErrorPopup("Invalid dates", [$T('Dates have an invalid format: dd/mm/yyyy hh:mm')], "");
                    popup.open();
                    return false
                }
                if ($E("createCategId").get() == "") {
                    var popup = new ErrorPopup($T('Missing mandatory data'), [$T('Please, choose a category (step 1)')], "");
                    popup.open();
                    return false;
                }
                if( editor.clean()){
                    $E('chairperson').set(Json.write(uf.getUsers()));
                    $E('description').set(editor.get());
                    injectFromProtectionChooser();
                    return true
                }
                return false;
        });

        verifyLectureDates();


    var editor = new ParsedRichTextWidget(600, 200, "", "rich");
    $E('descriptionBox').set(editor.draw());


    });


</script>
