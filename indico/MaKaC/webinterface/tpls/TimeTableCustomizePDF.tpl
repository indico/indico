
<br><br>
<form action=${ getPDFURL } method="post" target="_blank">
    <input type="hidden" name="showDays" value="${ showDays }">
    <input type="hidden" name="showSessions" value="${ showSessions }">
    <table width="80%" align="center" border="0">
        <tr>
            <td class="groupTitle"> ${ _("PDF timetable customisation")}</td>
        </tr>
        <tr>
          <td>
            <table width="100%">
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
                            <input type="checkbox" name="showCoverPage" value="showCoverPage" checked="checked"> ${ _("Print cover page")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showTableContents" value="showTableContents" checked="checked"> ${ _("Print Table of Contents")}
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
                            <input type="checkbox" name="showAbstract" value="showAbstract"> ${ _("Print ABSTRACT CONTENT of ALL the contributions")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="checkbox" name="dontShowPosterAbstract" value="showSessionTOC"> ${ _("Do NOT print the ABSTRACT CONTENT of poster sessions")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showLengthContribs" value="showLengthContribs"> ${ _("Show length of each contribution")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showSpeakerTitle" value="showSpeakerTitle" checked="checked"> ${ _("Print the TITLE of the speakers")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showSpeakerAffiliation" value="showSpeakerAffiliation">${ _("Print the affiliation of the speakers/conveners")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="newPagePerSession" value="newPagePerSession"> ${ _("Print each session on a new page")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="useSessionColorCodes" value="useSessionColorCodes" checked="checked">Use session color codes
                        </td>
                    </tr>
                    <!--<tr>
                        <td>
                            <input type="checkbox" name="showSessionDescription" value="showSessionDescription"> ${ _("Print DESCRIPTION for each session")}
                        </td>
                    </tr>-->
                    <tr>
                        <td>
                            <input type="checkbox" name="showContribsAtConfLevel" value="showContribsAtConfLevel" checked > ${ _("Print contributions which are not within any session")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showBreaksAtConfLevel" value="showBreaksAtConfLevel"> ${ _("""Print "breaks" which are not within any session""")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="printDateCloseToSessions" value="printDateCloseToSessions">${ _("Print the starting date close to sessions title")}
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
                            <input type="checkbox" name="showContribsAtConfLevel" value="showContribsAtConfLevel"> ${ _("Print contributions which are not within any session")}
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="checkbox" name="showBreaksAtConfLevel" value="showBreaksAtConfLevel"> ${ _("Print 'breaks' which are not within any session")}
                        </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr><td>${ commonPDFOptions }</td></tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td>
                <input type="submit" class="btn" value="${ _("get pdf")}" name="ok">
            </td>
        </tr>
    </table>
<br>
</form>
