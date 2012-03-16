<tr>
    <td>
        <form action=${ filterPostURL } method="POST">
            % if sortingField:
               <input type="hidden" name="sortBy" value='${_(sortingField)}'>
            % endif
            <div class="CRLDiv">
            <table width="100%" align="center" border="0">
                <tr>
                    <td>
                        <table width="100%">
                            <tr>
                                <td>
                                    <table align="center" cellspacing="10" width="100%">
                                        <tr>
                                            <td class="titleCellFormat" style="padding-right: 10px; border-bottom: 1px solid #888;">
                                                ${_("Types")}
                                            </td>
                                            <td class="titleCellFormat" style="padding-right: 10px; border-bottom: 1px solid #888;">
                                                ${ _("Sessions")}
                                            </td>
                                            <td class="titleCellFormat" style="padding-right: 10px; border-bottom: 1px solid #888;">
                                                ${_("Tracks")}
                                            </td>
                                        </tr>
                                        <tr>
                                            % if len(conf.getContribTypeList()) > 0:
                                                <td valign="top">
                                                    <input type="checkbox" name="typeShowNoValue" ${"checked" if filterCriteria.getField("type").getShowNoValue() else ""}>--${_("not specified")}--<br/>
                                                    % for type in conf.getContribTypeList():
                                                        <input type="checkbox" name="selTypes" value="${type.getId()}" ${"checked" if  type.getId() in filterCriteria.getField("type").getValues() else ""}>
                                                            ${type.getName()}
                                                        <br>
                                                    % endfor
                                                </td>
                                            % endif

                                            % if len(conf.getSessionListSorted()) > 0:
                                                <td valign="top">
                                                    <input type="checkbox" name="sessionShowNoValue" ${"checked" if filterCriteria.getField("session").getShowNoValue() else ""}>--${_("not specified")}--<br/>
                                                    % for session in conf.getSessionListSorted():
                                                        <input type="checkbox" name="selSessions" value="${session.getId()}" ${"checked" if  session.getId() in filterCriteria.getField("session").getValues() else ""}>
                                                            ${"(" + session.getCode() + ")" if session.getCode()!="no code" else ""}${session.getTitle()}
                                                        <br>
                                                    % endfor
                                                </td>
                                            % endif

                                            % if len(conf.getTrackList()) > 0:
                                                <td valign="top">
                                                    <input type="checkbox" name="trackShowNoValue" ${"checked" if filterCriteria.getField("track").getShowNoValue() else ""}>--${_("not specified")}--<br/>
                                                    % for track in conf.getTrackList():
                                                        <input type="checkbox" name="selTracks" value="${track.getId()}" ${"checked" if  type.getId() in filterCriteria.getField("track").getValues() else ""}>
                                                            ${"(" + track.getCode() + ")" if track.getCode() else ""}${track.getTitle()}
                                                        <br>
                                                    % endfor
                                                </td>
                                            % endif
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td align="center" style="padding: 5px; display: block">
                                    <input type="submit" class="btn" name="OK" value="${ _("apply")}"/>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table></div>
        </form></td>
</tr>