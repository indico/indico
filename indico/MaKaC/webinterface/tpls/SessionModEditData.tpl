<form id="SessionDataModificationForm" method="POST" action=${ postURL }>
  <table width="60%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
    <tr>
      <td colspan="2" class="groupTitle">${ pageTitle }</td>
    </tr>
    ${ code }
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat">${ _("Title")}</span><span class="mandatoryField">*</span></td>
      <td>
    <input id="sessionTitle" type="text" name="title" size="80" value=${ title }>
      </td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat">${ _("Description")}</span></td>
      <td>
    <textarea name="description" cols="80" rows="8" wrap="soft">${ description }</textarea>
      </td>
    </tr>


    <%include file="EventLocationInfo.tpl" args="event=self_._rh._target, modifying=True, parentRoomInfo=roomInfo(self_._rh._target, level='inherited'), showParent=True, conf = False, parentName=_('event')"/>

    <tr>
      <td class="titleCellTD"><span class="titleCellFormat">${ _("Start date")}</span></td>
      <td valign="top" bgcolor="white" width="100%">&nbsp;
      <span id="sDatePlace"></span>
                <input type="hidden" value="${ sDay }" name="sDay" id="sDay"/>
                <input type="hidden" value="${ sMonth }" name="sMonth" id="sMonth"/>
                <input type="hidden" value="${ sYear }" name="sYear" id="sYear"/>
                <input type="hidden" value="${ sHour }" name="sHour" id="sHour" />
                <input type="hidden" value="${ sMinute }" name="sMinute" id="sMinute" />
      ${ autoUpdate }
      </td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat">${ _("End date")}</span></td>
      <td valign="top" bgcolor="white" width="100%">&nbsp;
      <span id="eDatePlace"></span>
                <input type="hidden" value="${ eDay }" name="eDay" id="eDay"/>
                <input type="hidden" value="${ eMonth }" name="eMonth" id="eMonth"/>
                <input type="hidden" value="${ eYear }" name="eYear" id="eYear"/>
                <input type="hidden" value="${ eHour }" name="eHour" id="eHour" />
                <input type="hidden" value="${ eMinute }" name="eMinute" id="eMinute" />
      ${ adjustSlots }
      </td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat">${ _("Default contribution duration")}</span></td>
      <td bgcolor="white" width="100%">&nbsp;
      <input type="text" size="2" name="durHour" value=${ durHour } />:
      <input type="text" size="2" name="durMin" value=${ durMin } />
      </td>
    </tr>
    ${ Type }
    ${ Colors }
    ${ convener }
    <tr align="center">
      <td colspan="2" class="buttonBar" valign="bottom" align="center">
    <input type="submit" class="btn" value="${ _("ok")}" name="OK" id="ok" />
    <input type="submit" class="btn" value="${ _("cancel")}" name="CANCEL" />
      </td>
    </tr>
  </table>
</form>

<script type="text/javascript">
    var parameterManager = new IndicoUtil.parameterManager();
    parameterManager.add($E('sessionTitle'), 'text', false);

    $("#ok").click(function() {
        this.form.eDay.disabled = 0;
        this.form.eMonth.disabled = 0;
        this.form.eYear.disabled = 0;
        if (!parameterManager.check())
            event.preventDefault();
    });
IndicoUI.executeOnLoad(function()
    {
        var startDate = IndicoUI.Widgets.Generic.dateField(true,null,['sDay', 'sMonth', 'sYear','sHour', 'sMinute']);
        $E('sDatePlace').set(startDate);

        var endDate = IndicoUI.Widgets.Generic.dateField(true,null,['eDay', 'eMonth', 'eYear', 'eHour', 'eMinute']);
        $E('eDatePlace').set(endDate);

        % if sDay != '':
            startDate.set('${ sDay }/${ sMonth }/${ sYear } ${"0"+ sHour  if len (sHour) == 1 else  sHour }:${"0"+ sMinute  if len (sMinute) == 1 else  sMinute }');
        % endif

        % if eDay != '':
            endDate.set('${ eDay }/${ eMonth }/${ eYear } ${"0"+ eHour  if len (eHour) == 1 else  eHour }:${"0"+ eMinute  if len (eMinute) == 1 else  eMinute }');
        % endif
    });
    injectValuesInForm($E('SessionDataModificationForm'));

</script>
