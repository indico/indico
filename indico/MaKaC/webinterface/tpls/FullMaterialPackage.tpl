
<script type="text/javascript">
<!--
function selectAll()
{
    if (!document.getPkgForm.sessionList.length){
        document.getPkgForm.sessionList.checked=true
    } else {
        for (i = 0; i < document.getPkgForm.sessionList.length; i++) {
            document.getPkgForm.sessionList[i].checked=true
        }
    }
}

function deselectAll()
{
    if (!document.getPkgForm.sessionList.length)    {
        document.getPkgForm.sessionList.checked=false
    } else {
       for (i = 0; i < document.getPkgForm.sessionList.length; i++) {
           document.getPkgForm.sessionList[i].checked=false
       }
    }
}
//-->
</script>
<h3 class="groupTitle" style="background: rgb(229, 229, 229) none repeat scroll 0% 0%; -moz-background-clip: border; -moz-background-origin: padding; -moz-background-inline-policy: continuous; color: gray;">${ _("Get file package")}</h3>
<form action=${ getPkgURL } method="post" name="getPkgForm">
    <table width="100%">
        <tr>
            <td class="groupTitle"> ${ _("Contributions scheduled on")}:</td>
        </tr>
        <tr>
            <td>
                <table width="100%">
                    ${ dayList }
                </table>
            </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td>
              <table width="100%">
              <tr>
                <td valign="top" width="50%">
                  <table width="100%">
                  <tr>
                    <td class="groupTitle"> ${ _("Material type")}</td>
                  </tr>
                  <tr>
                    <td>
                      % for materialTypeName in materialTypes:
                      <div>
                        <input name="materialType" type="checkbox" value="${materialTypeName}" checked="checked"/>${_(materialTypeName.capitalize())}
                      </div>
                      % endfor
                      <input name="materialType" type="checkbox" value="other" checked="checked"/>${_("Other types")}
                    </td>
                  </tr>
                </table>
                </td>
                <td valign="top" width="100%">
                  <table width="100%"e>
                  <tr>
                    <td class="groupTitle"> ${ _("Sessions")}</td>
                  </tr>
                  <tr>
                    <td>
              <img src="${ selectAll }" border="0" alt="${ _("Select all")}" onclick="javascript:selectAll()">
              <img src="${ deselectAll }" border="0" alt="${ _("Deselect all")}" onclick="javascript:deselectAll()">&nbsp;<br>
                      ${ sessionList }
                    </td>
                  </tr>
                  </table>
                </td>
              </tr>
              </table>
          </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        % if self_._conf.getType() == "conference":
        <tr>
            <td class="groupTitle"> ${ _("Main Resource")}</td>
        </tr>
        <tr>
            <td>
                <input name="mainResource" type="checkbox" value="mainResource"> ${ _("Get only main resources from each material")}
            </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        % endif
        <tr>
            <td class="groupTitle"> ${ _("Get material")}...</td>
        </tr>
        <tr>
            <td>
                <table width="100%">
                    <tr>
                        <td>
                             ${ _("get only files added since")}
                            <input type="text" size="2" name="fromDay" value="dd">-
                            <input type="text" size="2" name="fromMonth" value="mm">-
                            <input type="text" size="4" name="fromYear" value="yyyy">
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td>
                <input type="submit" class="btn" value="${ _("get package")}" name="ok">
            </td>
        </tr>
    </table>
<br>
</form>
