<table width="90%" align="left" border="0">
${ withdrawnNotice }
<tr>
  <td>
    <table width="100%" align="left" border="0" style="border-right:1px solid #777777">
    <tr>
    </tr>
    <tr>
      <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Title")}</span></td>
      <td bgcolor="white" class="blacktext"><b>${ title }</b></td>
      <td align="right">
        <table border="0" cellspacing="1" cellpadding="0">
        <tr>
          <td bgcolor="white" align="right" width="10">
            <a href="${ contribXML }" target="_blank"><img src="${ xmlIconURL }" alt="${ _("print the current contribution")}" border="0"> </a>
          </td>
          <td bgcolor="white" align="right" width="10">
            <a href="${ contribPDF }" target="_blank"><img src="${ printIconURL }" alt="${ _("print the current contribution")}" border="0"> </a>
          </td>
        </tr>
        </table>
      </td>
      </tr>
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Description")}</span></td>
        <td bgcolor="white" class="blacktext">
                    ${ description }
                    </td>
        <form action="${ dataModificationURL }" method="POST">
        <td rowspan="2" valign="bottom" align="right" width="1%">
          <input type="submit" class="btn" value="modify">
        </td>
        </form>
      </tr>
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Place")}</span</td>
        <td bgcolor="white" class="blacktext">${ place }</td>
      </tr>
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Keywords")}</span</td>
        <td bgcolor="white" class="blacktext"><pre>${ keywords }</pre></td>
      </tr>
      <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
      </tr>
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Presenters")}</span</td>
        <td bgcolor="white" class="blacktext" colspan="2">
          <table>
          <tr>
            <td colspan="2" width="100%">
              <form action=${ remSpeakersURL } method="POST">
              ${ speakers }
            </td>
            <td valign="bottom" align="right">
              <table>
              <tr>
                <td>
                  <input type="submit" class="btn" name="remove" value="${ _("remove")}">
                </td>
                </form>
            <form action=${ newSpeakerURL } method="POST">
                <td>
              <input type="submit" class="btn" name="new" value="${ _("new")}">
                </td>
                </form>
        <form action=${ searchSpeakersURL } method="POST">
                <td>
                  <input type="submit" class="btn" name="search" value="${ _("search")}">
                </td>
              </tr>
              </table>
            </td>
            </form>
          </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
      </tr>
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Date/time")}</span</td>
        <td bgcolor="white" class="blacktext" colspan="2">${ dateInterval }</td>
      </tr>
      <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
      </tr>
      % if Config.getInstance().getReportNumberSystems():
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Report numbers")}</span</td>
        <td bgcolor="white" colspan="2">${ reportNumbersTable }</td>
      </tr>
      <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
      </tr>
      % endif
${ abstract }
${ withdrawnInfo }
            </table>
        </td>
    </tr>
</table>
