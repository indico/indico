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

<div class="groupTitle"> ${ _("Social bookmarks") }</div>
<table>
<tr>
    <td>
        <form action="${ socialFormURL }" method="POST">
        <table>
            <tr>
                  <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Active")}</span></td>
                  <td class="blacktext">
                          <select name="socialActive">
                              <option value="yes" ${"selected" if socialActive == True else ""}>
                                   ${ _("Yes")}
                              </option>
                              <option value="no" ${"selected" if socialActive == False else ""}>
                                   ${ _("No")}
                              </option>
                          </select>
                  </td>
            </tr>
            <tr>
                  <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Facebook App ID")}</span></td>
                  <td class="blacktext">
                    <input type="text" name="facebook_appId" value="${facebookData.get('appId', '')}" />
                  </td>
            </tr>
            <tr>
                <td>
                  <input type="submit" class="btn" value="${ _("save")}" style="margin-top: 10px;">
                </td>
            </tr>
        </table>
        </form>
    </td>
</tr>
</table>
