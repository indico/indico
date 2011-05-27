<table width="90%" border="0">
    ${ withdrawnNotice }
    <tr>
        <td>
            <table width="100%" align="left" border="0" style="border-right:1px solid #777777">
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Contribution ID")}</span></td>
                    <td bgcolor="white">${ id }</td>
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
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Title")}</span></td>
                    <td bgcolor="white" class="blacktext"><b>${ title }</b></td>
                    <form action="${ dataModificationURL }" method="POST">
                    <td rowspan="${ rowspan }" valign="bottom" align="right" width="1%">
                        <input type="submit" class="btn" value="${ _("modify")}">
                    </td>
                    </form>
                </tr>
                % if self_._rh._target.getConference().getAbstractMgr().isActive() and self_._rh._target.getConference().hasEnabledSection("cfa") and self_._rh._target.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
                ${ additionalFields }
                % else:
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Description")}</span></td>
                    <td bgcolor="white" class="blacktext">
                    ${ description }
                    </td>
                </tr>
                % endif
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Place")}</span</td>
                    <td bgcolor="white" class="blacktext">${ place }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Date/time")}</span</td>
                    <td bgcolor="white" class="blacktext" colspan="2">
              % if contrib.isScheduled():
                        ${ self_.htmlText(self_._contrib.getAdjustedStartDate().strftime("%A %d %B %Y %H:%M")) }
              % else:
                <em>${ _("Not scheduled")}</em>
              % endif
            </td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Duration")}</span</td>
                    <td bgcolor="white" class="blacktext">${ duration }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Type")}</span</td>
                    <td bgcolor="white" class="blacktext">${ type }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Keywords")}</span</td>
                    <td bgcolor="white" class="blacktext"><pre>${ keywords }</pre></td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                % if eventType == "conference":
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Track")}</span></td>
                    <td bgcolor="white" class="blacktext" colspan="2">
                        <table width="100%">
                            <tr>
                                <td width="100%">${ track }</td>
                                <form action=${ setTrackURL } method="POST">
                                <td valign="bottom" align="right">
                                    <select name="selTrack">${ selTracks }</select><input type="submit" class="btn" name="change" value="${ _("change")}">
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
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Session")}</span></td>
                    <td bgcolor="white" class="blacktext" colspan="2">
                        <table width="100%">
                            <tr>
                                <td width="100%">${ session }</td>
                                <form action=${ setSessionURL } method="POST">
                                <td valign="bottom" align="right">
                                    <select name="selSession">${ selSessions }</select><input type="submit" class="btn" name="change" value="${ _("change")}">
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
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Primary authors")}</span></td>
                    <td colspan="2">
                        <table width="100%">
                            <tr>
                                <td style="width: 79%"><ul id="inPlacePrimaryAuthors" class="UIPeopleList"></ul></td>
                                <td nowrap valign="top" style="width: 21%; text-align:right;">
                                    <span id="inPlacePrimaryAuthorsMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                                        <a class="dropDownMenu fakeLink"  style="margin-left: 15px; margin-right: 15px" onclick="primaryAuthorManager.addManagementMenu();">${ _("Add primary author")}</a>
                                    </span>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Co-authors")}</span></td>
                    <td colspan="2">
                        <table width="100%">
                            <tr>
                                <td style="width: 79%"><ul id="inPlaceCoAuthors" class="UIPeopleList"></ul></td>
                                <td nowrap valign="top" style="width: 21%; text-align:right;">
                                    <span id="inPlaceCoAuthorsMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                                        <a class="dropDownMenu fakeLink"  style="margin-left: 15px; margin-right: 15px" onclick="coAuthorManager.addManagementMenu();">${ _("Add co-author")}</a>
                                    </span>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                % endif
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Presenters") if eventType == "conference" else  _("Speakers")}</span></td>
                    <td bgcolor="white" class="blacktext" colspan="2">
                        <table width="100%">
                            <tr>
                                <td style="width: 79%"><ul id="inPlaceSpeakers" class="UIPeopleList"></ul></td>
                                <td nowrap valign="top" style="width: 21%; text-align:right;">
                                    <span id="inPlaceSpeakersMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                                        <a class="dropDownMenu fakeLink"  style="margin-left: 15px; margin-right: 15px" onclick="speakerManager.addManagementMenu();">${ _("Add presenter") if eventType == "conference" else  _("Add speakers")}</a>
                                    </span>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Report numbers")}</span</td>
                    <td bgcolor="white" colspan="2"><i>${ reportNumbersTable }</i></td>
                </tr>
                <tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                % if eventType == "conference":
                ${ abstract }
                ${ withdrawnInfo }
                <tr>
                    <td align="center" colspan="3" style="border-top: 2px solid #777777">
                        <table align="center" border="0">
                            <tr>
                                % if withdrawDisabled:
                                <form action=${ withdrawURL } method="POST">
                                <td>
                                    ${ _("This contribution is withdrawn:")}
                                    <input type="submit" class="btn" name ="REACTIVATE" value="reactivate">
                                </td>

                                % endif
                                % if not withdrawDisabled:

                                <form action=${ withdrawURL } method="POST">
                                <td>
                                    <input type="submit" class="btn" value="${ _("withdraw")}">
                                </td>
                                   % endif
                            </tr>
                        </table>
                    </td>
                </tr>
                % endif

            </table>
        </td>
    </tr>
</table>

<script>

% if eventType == "conference":
    var primaryAuthorManager = new ParticipantsListManager('${ self_._rh._target.getConference().getId() }',
        '${ id }', $E('inPlacePrimaryAuthors'), $E('inPlacePrimaryAuthorsMenu'), "prAuthor", "primary author", "conference");

    var coAuthorManager = new ParticipantsListManager('${ self_._rh._target.getConference().getId() }',
        '${ id }', $E('inPlaceCoAuthors'), $E('inPlaceCoAuthorsMenu'), "coAuthor", "co-author", "conference");

    var speakerManager = new ParticipantsListManager('${ self_._rh._target.getConference().getId() }',
            '${ id }', $E('inPlaceSpeakers'), $E('inPlaceSpeakersMenu'), "speaker", "presenter", "conference", "UIPerson");

    // To allow change elements between lists and reload the others list when an action is executed
    primaryAuthorManager.setComplementariesList(coAuthorManager, speakerManager);
    coAuthorManager.setComplementariesList(primaryAuthorManager, speakerManager);
    speakerManager.setComplementariesList(primaryAuthorManager, coAuthorManager);

% else:
    var speakerManager = new ParticipantsListManager('${ self_._rh._target.getConference().getId() }',
            '${ id }', $E('inPlaceSpeakers'), $E('inPlaceSpeakersMenu'), "speaker", "speaker", "meeting", "UIPerson");

% endif

</script>



