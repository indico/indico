<div class="groupTitle"> ${ _("Templates") }</div>
<table>
<tr>
    <td>
        <form action="${ templateSetFormURL }" method="POST">
        <table>
            <tr>
                  <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Template Set")}</span></td>
                  <td class="blacktext">
                          <select name="templateSet">
                              <option value="None" ${"selected" if defaultTemplateSet == None else ""}>
                                   ${ _("Default")}
                              </option>
                              % for template in availableTemplates:
                                  <option value="${ template }" ${ "selected" if defaultTemplateSet == template else ""}>
                                      ${ template }
                                  </option>
                              % endfor
                          </select>
                  </td>
                <td>
                  <input type="submit" class="btn" value="${ _("save")}">
                </td>
            </tr>
        </table>
        </form>
    </td>
</tr>
</table>

