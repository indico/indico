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
        if (!parameterManager.check())
            event.preventDefault();
    });
    injectValuesInForm($E('SessionDataModificationForm'));

</script>
