<form action='${ CreatePDFURL }' method='post' target='_blank'>
  <table class="gestiontable" style="text-align: left; width: 100%;" border="0" cellpadding="0">
    <tbody>
      <tr>
        <td colspan="1" class="subgroupTitle"> ${ _("Badge Printing")}</td>
      </tr>

      <tr>
        <td>
          <input class="btn" value="${ _("Print Badges")}" type="submit">
        </td>
      </tr>

      <tr>
        <td>
          &nbsp;
        </td>
      </tr>

      <tr>
        <td class="groupTitle">
           ${ _("List of available templates")}:
        </td>
      </tr>

      <tr>
        <td>
          <table class="gestiontable" width="50%">
            <tbody>
${ templateList }
          </table>
        </td>
      </tr>

      <tr>
          <td>
          <a href="${ badgeDesignURL }"> ${ _("Badge template design")}</a>
        </td>
      </tr>
    </tbody>
  </table>

  <table width="100%" class="gestiontable" style="margin-top:1em; margin-bottom:1em;">
    <tbody>
      <tr>
        <td class="groupTitle">
          <span>${ _("PDF Options")}</span>
        </td>
      </tr>
    ${ PDFOptions }
    </tbody>
  </table>

  <table class="gestiontable" style="text-align: left; width: 100%;" border="0" cellpadding="0">
    <tbody><tr><td>
      <div style="border-top:1px solid; margin-right: 10px;">
        <strong><em>${ _("Printing badges for:")}</em></strong><br />
        ${ registrantNamesList }
        <input type="hidden" name="registrantList" value="${ registrantList }"/>
      </div>
    </td></tr></tbody>
  </table>
</form>
