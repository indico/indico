<table width="90%" align="left" border="0">
  <tr>
    <td>
      <table width="100%" align="left" border="0">
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Registrant ID")}</span></td>
          <td bgcolor="white">${ id }</td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Registration date")}</span></td>
          <td bgcolor="white" class="blacktext">${ registrationDate }</td>
        </tr>
        <tr>
          <td colspan="3" class="horizontalLine">&nbsp;</td>
        </tr>
        ${ sections }
        ${ statuses }
        ${ transaction }
      </table>
    </td>
  </tr>
</table>
