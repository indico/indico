<div class="container" style="max-width: 1000px; overflow: visible;">
<form id="eventCreationForm" action="${ postURL }"  method="POST">
    <input type="hidden" name="event_type" value="${ event_type }">
    <input type="hidden" name="sessionSlots" value="disabled"/>

    <em>${ _("Please follow the steps to create a meeting")}</em>

    <div class="groupTitle">${ _("Step 1: Choose a category")}</div>

    <div style="padding: 10px">
        <input type="hidden" value="${ categ['id'] }" name="categId" id="createCategId"/>
        <span class="selectedCategoryName">${ _("The event will be created in:")} <span id="categTitle" class="categTitleChosen">${ categ['title'] }</span></span><input ${'style="display: none;"' if nocategs else ""} id="buttonCategChooser" type="button" value="${ _("Browse...")}" onclick="openCategoryChooser()"/>
    </div>

    <div class="groupTitle">${ _("Step 2: Enter basic information about the meeting") }</div>

    <table class="groupTable">
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Title")}</span></td>
            <td nowrap class="contentCellTD">
                    <input type="text" name="title" size="80" value="${ title }">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Start date")}</span></td>
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
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("End date")}</span></td>
            <td class="contentCellTD">
                <span id="eDatePlace"></span>
                <input type="hidden" value="" name="eDay" id="eDay"/>
                <input type="hidden" value="" name="eMonth" id="eMonth"/>
                <input type="hidden" value="" name="eYear" id="eYear"/>
                <input type="hidden" id="eHour" name="eHour" value="">
                <input type="hidden" id="eMinute" name="eMinute" value="">
                <span><a href="#" onclick="new ShowConcurrentEvents(createDatesDict()).execute()">${ _("Show existing events during these dates")}</a></span>
            </td>
        </tr>
        <!-- Fermi timezone awareness -->
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Timezone")}</span></td>
            <td class="contentCellTD">
                <select id="Timezone" name="Timezone">${ timezoneOptions }</select>
            </td>
        </tr>
        <!-- Fermi timezone awareness(end) -->

        <%include file="EventLocationInfo.tpl" args="modifying=False, showParent=False, conf = False"/>

        <tr>
            <td>&nbsp;</td>
            <td class="contentCellTD" style="font-style: italic; padding-top: 10px;"><span id="advancedOptionsText" class="fakeLink">&nbsp;</span></td>
        </tr>

        <tr id="advancedOptions" style="display:none"><td colspan="2">

            <table class="groupTable">
            <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat">${ _("Description")}</span>
                <input type="hidden" id="description" name="description" value="">
            </td>
            <td nowrap  class="contentCellTD" id="descriptionBox">
            </td>
            </tr>
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Default layout style")}</span></td>
                <td  class="contentCellTD">
                    <select name="defaultStyle">${ styleOptions }</select>
            </td>
            </tr>

            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Chairperson") }</span></td>
                <%include file="EventParticipantAddition.tpl"/>
            </tr>
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Keywords")}<br><small>(${ _("one per line")})</small></span></td>
                <td nowrap class="contentCellTD">
                    <textarea name="keywords" cols="60" rows="3">${ keywords }</textarea>
                </td>
            </tr>
            </table>
        </td></tr>
    </table>

    <%include file="EventSetProtection.tpl" args="eventType='meeting'"/>

    <table class="groupTable" style="background-color: #ECECEC; border-top: 1px dashed #777777;">
        <tr>
            <td width="15%" nowrap>&nbsp;</td>
            <td nowrap  style="padding: 10px 0;">
                <input style="font-weight: bold;" type="submit" name="ok" value="${ _("Create meeting")}">
            </td>
        </tr>
    </table>


</form>
</div>
<%include file="EventCreationJS.tpl"/>

<script  type="text/javascript">
    // ----- show concurrent events
    function createDatesDict() {
        if (verifyDates()) {

            var res = {};

            res["sDate"] = Util.formatDateTime(dates.item(0).get(), IndicoDateTimeFormats.Server, IndicoDateTimeFormats.Default);
            res["eDate"] = Util.formatDateTime(dates.item(1).get(), IndicoDateTimeFormats.Server, IndicoDateTimeFormats.Default);
            res["timezone"] = $E('Timezone').get();

            return res;
        }else{
            var popup = new ErrorPopup('${ _("Invalid dates")}', ["${ _("Dates have an invalid format: dd/mm/yyyy hh:mm")}"], "");
            popup.open();
            return null;
        }

    }

    // ----- Categ Chooser
    var categoryChooserHandler = function(categ, protection){
        $E("createCategId").set(categ.id);
        $E("categTitle").set(categ.title);
        $E("buttonCategChooser").set("${ _("Change...")}");
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
        showAdvancedOptions();

        if ("${categ["id"]}" != ""){
            $E("buttonCategChooser").set("${ _("Change...")}");
        }

        protectionChooserExecOnLoad("${ categ["id"] }", "${ protection }");

        var startDate = IndicoUI.Widgets.Generic.dateField(true,null,['sDay', 'sMonth', 'sYear','sHour', 'sMinute']);
        $E('sDatePlace').set(startDate);

        var endDate = IndicoUI.Widgets.Generic.dateField(true,null,['eDay', 'eMonth', 'eYear', 'eHour', 'eMinute']);
        $E('eDatePlace').set(endDate);

        % if sDay != '':
            startDate.set('${ sDay }/${ sMonth }/${ sYear } ${ sHour }:${ sMinute }');
        % endif

        % if eDay != '':
            endDate.set('${ eDay }/${ eMonth }/${ eYear } ${ eHour }:${ eMinute }');
        % endif

        dates.append(startDate);
        dates.append(endDate);

        injectValuesInForm($E('eventCreationForm'),function() {
                if (verifyDates()) {
                    var sDate = Util.parseJSDateTime(dates.item(0).get(), IndicoDateTimeFormats.Default);
                    var eDate = Util.parseJSDateTime(dates.item(1).get(), IndicoDateTimeFormats.Default);
                    if (showDatesStorageErrorPopup(sDate, eDate)) {
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
                    return true;
                }
                return false;
        });

    verifyDates();

    var editor = new ParsedRichTextWidget(600, 200, "", "rich");
    $E('descriptionBox').set(editor.draw());
    });

</script>
