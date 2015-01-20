<form id="eventModificationForm" action="${ postURL }" method="POST">
    <input type="hidden" name="event_type" value="${ event_type }">
    <table class="groupTable">
        <tr>
            <td colspan="2"><div class="groupTitle">${ _("Modify event data")}</div></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}</span></td>
            <td bgcolor="white" width="100%">
                    <input type="text" name="title" size="80" value=${ title }>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Description")}</span></td>
            <td bgcolor="white" width="100%">
                <textarea name="description" cols="70" rows="12" wrap="soft">${ description }</textarea>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Keywords<br><small>( ${ _("one per line")})</small></span></td>
            <td bgcolor="white" width="100%">
                <textarea name="keywords" cols="70" rows="3">${ keywords }</textarea>
            </td>
        </tr>

    <%include file="EventLocationInfo.tpl" args="event=self_._rh._target, modifying=True, showParent=False, conf=False"/>

        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Start date")}</span></td>
            <td bgcolor="white" width="100%">
                <span id="sDatePlace"></span>
                <input type="hidden" value="${ sDay }" name="sDay" id="sDay"/>
                <input type="hidden" value="${ sMonth }" name="sMonth" id="sMonth"/>
                <input type="hidden" value="${ sYear }" name="sYear" id="sYear"/>
                <input type="hidden" value="${ sHour }" name="sHour" id="sHour" />
                <input type="hidden" value="${ sMinute }" name="sMinute" id="sMinute" />
                % if conference.getType() != "simple_event":
                &nbsp;<input type="checkbox" name="move" value="1" checked>  ${ _("move timetable content")}
                % endif
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("End date")}</span></td>
            <td bgcolor="white" width="100%">
                <span id="eDatePlace"></span>
                <input type="hidden" value="${ eDay }" name="eDay" id="eDay"/>
                <input type="hidden" value="${ eMonth }" name="eMonth" id="eMonth"/>
                <input type="hidden" value="${ eYear }" name="eYear" id="eYear"/>
                <input type="hidden" value="${ eHour }" name="eHour" id="eHour" />
                <input type="hidden" value="${ eMinute }" name="eMinute" id="eMinute" />
            </td>
        </tr>
        <!-- Fermi timezone awareness -->
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Timezone</span></td>
            <td bgcolor="white" width="100%">
              <select name="Timezone">
              ${ timezoneOptions }
              </select>
            </td>
        </tr>
        <!-- Fermi timezone awareness(end) -->
${ additionalInfo }
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Support caption")}</span></td>
            <td bgcolor="white" width="100%"><input type="text" name="supportCaption" value=${ supportCaption } size="50"></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Support email")}</span></td>
            <td bgcolor="white" width="100%"><input type="text" name="supportEmail" value=${ supportEmail } size="50"></td>
        </tr>
        <!-- TO REMOVE CHAIRPERSON TEXT -->
        % if conference.getType() != "simple_event" and chairText != '""':
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Chairperson text")}</span></td>
            <td bgcolor="white" width="100%">
                <input type="text" name="chairText" id="chairText" value=${ chairText } size="50" disabled="disabled">
                <span id="removeChairpersonText"></span>
                ${inlineContextHelp(_("Chairperson text is deprecated, use chairpersons list instead.<br>Click on the red cross to remove the text.") )}
            </td>
        </tr>
        % endif
        % if conference.getType() == "simple_event":
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Organisers</span></td>
            <td bgcolor="white" width="100%">
                <input type="text" name="orgText" value=${ orgText } size="50">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Internal Comments</span></td>
            <td bgcolor="white" width="100%">
                <textarea name="comments" cols=50 rows=5>${ conference.getComments() }</textarea>
            </td>
        </tr>
        % endif
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Timetable default style")}</span></td>
            <td bgcolor="white" width="100%"><select name="defaultStyle">${ styleOptions }</select></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Visibility")}</span></td>
            <td bgcolor="white" width="100%">
              <select name="visibility">
              ${ visibility }
              </select>
        </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Event type")}</span></td>
            <td bgcolor="white" width="100%">
              <select name="eventType">
              ${ types }
              </select>
        </td>
        </tr>
        % if Config.getInstance().getShortEventURL() != "" :
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Short URL tag</span></td>
            <td bgcolor="white" width="100%">
                <span class="blacktext"><em> ${Config.getInstance().getShortEventURL() }</em></span>
                <span id="shortTag"></span>
            </td>
        </tr>
        % endif
        <tr align="left">
            <td class="buttonBar" align="center" width="100%" colspan="2">
            <span id="submitPlace"></span>
            </td>
        </tr>
    </table>
</form>

<script  type="text/javascript">

        IndicoUI.executeOnLoad(function()
    {
        var parameterManager = new IndicoUtil.parameterManager();

        var startDate = IndicoUI.Widgets.Generic.dateField(true,null,['sDay', 'sMonth', 'sYear','sHour', 'sMinute']);
        $E('sDatePlace').set(startDate);

        var endDate = IndicoUI.Widgets.Generic.dateField(true,null,['eDay', 'eMonth', 'eYear', 'eHour', 'eMinute']);
        $E('eDatePlace').set(endDate);

        % if conference.getType() != "simple_event" and chairText != '""':
            var removeChairpersonTextButton = Html.img({src: imageSrc("remove.png")});
            removeChairpersonTextButton.observeClick( function(){
                $E('chairText').dom.value = "";
            });

            $E('removeChairpersonText').set(removeChairpersonTextButton);
        % endif

        % if sDay != '':
            startDate.set('${ sDay }/${ sMonth }/${ sYear } ${"0"+ sHour  if len (sHour) == 1 else  sHour }:${"0"+ sMinute  if len (sMinute) == 1 else  sMinute }');
        % endif

        % if eDay != '':
            endDate.set('${ eDay }/${ eMonth }/${ eYear } ${"0"+ eHour  if len (eHour) == 1 else  eHour }:${"0"+ eMinute  if len (eMinute) == 1 else  eMinute }');
        % endif

        var shortTags = Html.input('text', {name: "shortURLTag", size: "30"}, ${ shortURLTag });
        $E('shortTag').set(shortTags);

        var submitButton = Html.input('submit', {className: 'btn'}, $T("ok"));
        var cancelButton = Html.input('button', {className: 'btn', name: 'cancel'}, $T("cancel"));
        $E('submitPlace').set(submitButton, cancelButton);

        submitButton.observeClick(function(){
            if (!parameterManager.check()) {
                return false;
            }
        });

        cancelButton.observeClick(function(){
            document.getElementById('eventModificationForm').submit();
        });

        parameterManager.add(shortTags, 'shortURL', true);

        injectValuesInForm($E('eventModificationForm'));
    });

</script>
