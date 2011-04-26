<br><br>
<form id="pdfForm" action=${ getPDFURL } method="post">
    <input type="hidden" name="showDays" value="${ showDays }">
    <input type="hidden" name="showSessions" value="${ showSessions }">
    <table width="40%" align="center" border="0" style="background-color: white; border-left: 1px solid #777777; border-top: 1px solid #777777;">
        <tr>
            <td class="groupTitle" style="background:#E5E5E5; color:gray"> ${ _("PDF timetable customisation")}</td>
        </tr>
        <tr>
          <td>
            <table width="100%" style="padding:20px;">
              <tr>
                <td>
                  <input type="radio" name="typeTT" value="normalTT" checked><b> ${ _("Normal timetable")}:</b>
                </td>
              </tr>
              <tr>
                <td>
                  <table width="100%" style="padding-left:20px">
                    <tr>
                        <td>
                            <input type="checkbox" name="showCoverPage" value="showCoverPage"> ${ _("Print cover page")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showTableContents" value="showTableContents"> ${ _("Print Table of Contents")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="checkbox" name="showSessionTOC" value="showSessionTOC" checked="checked"> ${ _("Show sessions in the Table Of Contents")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showContribId" value="showContribId" checked="checked"> ${ _("Print the ID of the contribution")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showAbstract" value="showAbstract"> ${ _("Print CONTENT of the contributions")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showLengthContribs" value="showLengthContribs" checked="checked"> ${ _("Show length of each contribution")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showSpeakerTitle" value="showSpeakerTitle" checked="checked"> ${ _("Print the TITLE of the speakers")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="newPagePerSession" value="newPagePerSession"> ${ _("Print each session on a new page")}
                        </td>
                    </tr>
                    <!--<tr>
                        <td>
                            <input type="checkbox" name="showSessionDescription" value="showSessionDescription"> ${ _("Print DESCRIPTION for each session")}
                        </td>
                    </tr>-->
                    <tr>
                        <td>
                            <input type="checkbox" name="showContribsAtConfLevel" value="showContribsAtConfLevel" checked="checked"> ${ _("Print contributions which are not within any session")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showBreaksAtConfLevel" value="showBreaksAtConfLevel" checked="checked"> ${ _("Print 'breaks' which are not within any session")}
                        </td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td>
                  <input type="radio" name="typeTT" value="simpleTT"><b> ${ _("Simplified timetable")}</b>
                </td>
              </tr>
              <tr>
                <td>
                  <table width="100%" style="padding-left:20px">
                    <tr>
                        <td>
                            <input type="checkbox" name="showContribsAtConfLevel" value="showContribsAtConfLevel" checked="checked"> ${ _("Print contributions which are not within any session")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showBreaksAtConfLevel" value="showBreaksAtConfLevel" checked="checked"> ${ _("Print 'breaks' which are not within any session")}
                        </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td>
                <input type="submit" class="btn" value="${ _("get pdf")}" name="action" />&nbsp;
                <input type="submit" class="btn" value="${ _("cancel") }" id="cancel" name="cancel" />
            </td>
        </tr>
    </table>
<br>
</form>
