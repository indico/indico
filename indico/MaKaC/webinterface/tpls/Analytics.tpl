<div class="groupTitle"> ${ _("Configuration") }</div>
<table>
<tr>
    <td>
        <form action="${ analyticsFormURL }" method="POST">
        <table>
            <tr>
                  <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Active")}</span></td>
                  <td class="blacktext">
                          <select name="analyticsActive">
                              <option value="yes" ${"selected" if analyticsActive == True else ""}>
                                   ${ _("Yes")}
                              </option>
                              <option value="no" ${"selected" if analyticsActive == False else ""}>
                                   ${ _("No")}
                              </option>
                          </select>
                  </td>
            </tr>
            <tr>
                  <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Analytics Code")}</span></td>
                  <td class="blacktext" width="90%">
                      <span style="font-style:italic;"> ${_("Please paste the code you want to include in the text area below:")}</span><br/>
                      <textarea cols="80" rows="8" name="analyticsCode">${analyticsCode}</textarea>
                    <span id="analyticsHelp" style="display:block; color:red; font-style:italic">
                    ${_("Please exercise caution when using the code noted above as it will be included in every page thereafter. A consequence of this may be that it breaks the remaining application code.")}
                    </span>
                  </td>

            </tr>
            <tr>
                  <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Analytics Code Location")}</span></td>
                  <td class="blacktext" width="90%">
                  <input type="radio" name="analyticsCodeLocation" value="head" ${"checked" if analyticsCodeLocation=="head" else ""}>${_("Head")}
                  <input type="radio" name="analyticsCodeLocation" value="body" ${"checked" if analyticsCodeLocation=="body" else ""}>${_("Body")}
                  </td>

            </tr>
            <tr><td></td>
                <td>
                  <input type="submit" class="btn" value="${ _("save")}" style="margin-top: 10px;">
                </td>
            </tr>
        </table>
        </form>
    </td>
</tr>
</table>