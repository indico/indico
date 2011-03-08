  <table class="gestiontable" style="text-align: left; width: 95%;" border="0" cellpadding="0">
    <tbody>
      <tr>
        <td colspan="2" class="subgroupTitle">${ _("Poster Printing")}</td>
      </tr>

      <tr>
        <td  colspan="2">
          &nbsp;
        </td>
      </tr>
      <tr>
        <td  colspan="2" class="groupTitle">
           ${ _("Create poster")}
        </td>
      </tr>
      <form action='${ CreatePDFURL }' method='post' target='_blank'>
      <tr>
          <td class="titleCellTD" NOWRAP>
            ${ _("Based on:")}
          </td>
        <td>
          <select name="templateId">
          ${ fullTemplateList }
          </select>
          <input class="btn" value="${ _("Create Poster From Template")}" type="submit">
        </td>
      </tr>
      <tr>
          <td class="titleCellTD" NOWRAP>
            ${ _("PDF Options:")}
          </td>
        <td>
        ${ PDFOptions }
        </td>
      </tr>
</form>
<form action='${ NewTemplateURL }' method='post'>
      <tr>
        <td colspan="2" class="groupTitle">
           ${ _("Local poster templates (templates attached to this specific event)")}
        </td>
      </tr>

      <tr>
        <td colspan="2">
          <table class="gestiontable" width="50%">
            <tbody>
${ templateList }
          </table>
        </td>
      </tr>
     <tr>
         <td></td>
        <td>
          <select name="baseTemplate">
          ${ baseTemplateList }
          </select>
          <input name="New Template Button" class="btn" value="${ _("New")}" type="submit">
        </td>
     </tr>
    </tbody>
  </table>
</form>