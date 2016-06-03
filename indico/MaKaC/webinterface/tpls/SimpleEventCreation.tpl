<div class="container" style="max-width: 1000px; overflow: visible;">
<form class="i-form" id="eventCreationForm" action="${ postURL }" method="POST">

    <input type="hidden" name="event_type" value="${ event_type }">
    <input type="hidden" name="csrf_token" value="${ _session.csrf_token }">

    <em>${ _("Please follow the steps to create a lecture")}</em>
    <div class="groupTitle">${ _("Step 1: Choose a category")}</div>
    <table class="groupTable" id="event-creation-category-field">
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat">${ _("Category")}</span>
            </td>
            <td>
                <div class="form-group">
                    <div class="form-field">
                        ${ template_hook('event-category-field') }
                    </div>
                </div>
            </td>
        </tr>
    </table>

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
                <span class="titleCellFormat">${ _("Speakers") }</span>
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

    // ---- On Load

    IndicoUI.executeOnLoad(function()
    {

        initializeDatesContainer();

        showAdvancedOptions();

        var $category = $('#event-creation-category-field #category');
        $category.on('indico:categorySelected', function(evt, category) {
            updateProtectionChooser(category.title, category.is_protected ? 'private' : 'public');
        });
        protectionChooserExecOnLoad('', '');

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
                if (!$category.val()) {
                    var popup = new ErrorPopup($T('Missing mandatory data'), [$T('Please, choose a category (step 1)')], "");
                    popup.open();
                    return false;
                }
                if( editor.clean()){
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
