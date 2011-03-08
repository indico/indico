<% from MaKaC.i18n import _ %>

<div class="groupTitle"> ${ _("Templates") }</div>
<table align="center" width="100%">
<tr>
    <td>
        <form action="${ formURL }" method="POST">
        <table width="100%" align="center" border="0">
            <tr>
                  <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Template Set")}</span></td>
                  <td bgcolor="white" valign="top" class="blacktext">
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
                        <input type="submit" class="btn" value="${ _("change")}">
                </td>
            </tr>
        </table>
        </form>
    </td>
</tr>
</table>