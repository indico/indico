<table width="90%%" align="left" border="0">
%(withdrawnNotice)s
<tr>
  <td>
    <table width="100%%" align="left" border="0" style="border-right:1px solid #777777">
    <tr>
    </tr>
    <tr>
      <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
      <td bgcolor="white" class="blacktext"><b>%(title)s</b></td>
      <td align="right">
        <table border="0" cellspacing="1" cellpadding="0">
        <tr>
          <td bgcolor="white" align="right" width="10">
            <a href="%(contribXML)s" target="_blank"><img src="%(xmlIconURL)s" alt="<%= _("print the current contribution")%>" border="0"> </a>
          </td>
          <td bgcolor="white" align="right" width="10">
            <a href="%(contribPDF)s" target="_blank"><img src="%(printIconURL)s" alt="<%= _("print the current contribution")%>" border="0"> </a>
          </td>
        </tr>
        </table>
      </td>
      </tr>
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Description")%></span></td>
        <td bgcolor="white" class="blacktext">
                    %(description)s
                    </td>
        <form action="%(dataModificationURL)s" method="POST">
        <td rowspan="2" valign="bottom" align="right" width="1%%">
          <input type="submit" class="btn" value="modify">
        </td>
        </form>
      </tr>
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Place")%></span</td>
        <td bgcolor="white" class="blacktext">%(place)s</td>
      </tr>
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Keywords")%></span</td>
        <td bgcolor="white" class="blacktext"><pre>%(keywords)s</pre></td>
      </tr>
      <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
      </tr>
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Presenters")%></span</td>
        <td bgcolor="white" class="blacktext" colspan="2">
          <table>
          <tr>
            <td colspan="2" width="100%%">
              <form action=%(remSpeakersURL)s method="POST">
              %(speakers)s
            </td>
            <td valign="bottom" align="right">
              <table>
              <tr>
                <td>
                  <input type="submit" class="btn" name="remove" value="<%= _("remove")%>">
                </td>
                </form>
	        <form action=%(newSpeakerURL)s method="POST">
                <td>
	          <input type="submit" class="btn" name="new" value="<%= _("new")%>">
                </td>
                </form>
		<form action=%(searchSpeakersURL)s method="POST">
                <td>
                  <input type="submit" class="btn" name="search" value="<%= _("search")%>">
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
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Date/time")%></span</td>
        <td bgcolor="white" class="blacktext" colspan="2">%(dateInterval)s</td>
      </tr>
      <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
      </tr>
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Report numbers")%></span</td>
        <td bgcolor="white" colspan="2"><i>%(reportNumbersTable)s</i></td>
      </tr>
      <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
      </tr>
%(abstract)s
%(withdrawnInfo)s
            </table>
        </td>
    </tr>
</table>
