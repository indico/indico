<div style="float:right;">
  <ul class="horizontalMenu">

    <%include file="LoginWidget.tpl"/>
  </ul>
</div>


<table>
    <tr>
        <form style="margin:0pt;" action="">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr class="bluerowheader">
            <td colspan="4"></td>
          </tr>
          <tr>
            <td class="bluerowheader">
              <a href="${ MaKaCHomeURL }">
                <img class="imglink" src="${ imgLogo }" alt="indico">
              </a>
            </td>
            <td width="100%">
              <small>
              <input type="hidden" name="confId" value="${ confId }">
              &nbsp;<a href="${ categurl }">${ _("event home page")}</a>&nbsp;
              ${ menu }
              &nbsp;|&nbsp;
              ${ confModif }&nbsp;
                  &nbsp;<a href=${ printURL }><img src=${ printIMG } alt="${ _("printable view (w/o menus and icons)")}" title="${ _("printable view (w/o menus and icons)")}" style="border:0px;vertical-align:middle;padding-bottom:2px"></a>\
                  &nbsp;<a href=${ pdfURL }><img src=${ pdfIMG } alt="${ _("create PDF")}" title="${ _("create PDF")}" style="border:0px;vertical-align:middle;padding-bottom:2px"></a>
                  &nbsp;<a href=${ matPackURL }><img src=${ zipIMG } alt="${ _("get material package")}" title="${ _("get material package")}" style="border:0px;vertical-align:middle;padding-bottom:2px"></a>
              ${"&nbsp;|&nbsp;" if evaluation.strip()!="" else ""}
              ${ evaluation }
              </small>
            </td>
            </form>
            <td>${ TZSelector }</td>
           </tr>
        </table>
    </tr>
</table>
