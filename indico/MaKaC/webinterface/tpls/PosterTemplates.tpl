
  <table class="groupTable" cellpadding="0">
    <tbody>
      <tr>
        <td colspan="1" class="subgroupTitle"> ${ _("Poster Default Templates")}</td>
      </tr>
      <tr>
        <td class="groupTitle">
           ${ _("List of default templates")}
        </td>
      </tr>

      <tr>
        <td>
          <input name="New Template Button" class="btn" value="${ _("New")}" type="button" onClick="location.href='${ NewDefaultTemplateURL }'">
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

    </tbody>
  </table>
