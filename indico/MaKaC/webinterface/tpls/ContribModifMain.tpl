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
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Primary authors")}</span</td>
                    <td bgcolor="white" class="blacktext" colspan="2">${ primAuthTable }</td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Co-authors")}</span</td>
                    <td bgcolor="white" class="blacktext" colspan="2">${ coAuthTable }</td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                % endif
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Presenters") if eventType == "conference" else  _("Speakers")}</span</td>
                    <td bgcolor="white" class="blacktext" colspan="2">
                        <table width="100%">
                            <tr>
                                <td colspan="2" width="100%">
                                    <form style="padding:0px;margin:0px;" action=${ remSpeakersURL } method="POST">
                                        ${ speakers }
                                </td>
                                <td valign="bottom" align="right">
                                        <input type="submit" class="btn" name="remove" value="${ _("remove")}">
                                    </form>
                                    % if eventType == "conference":
                                    <form style="padding:0px;margin:0px;" action=${ addSpeakersURL } method="POST">
                                        <table cellspacing="0px" cellpadding="0px" border="0"><tr><td>
                                        <select name="selAuthor">${ authorsForSpeakers }</select></td>
                                        <td><input type="submit" class="btn" name="add" value="${ _("add")}">
                                        </td></tr></table>
                                    </form>
                                    % endif
                                    <form style="padding:0px;margin:0px;" action=${ newSpeakerURL } method="POST">
                                        <input type="submit" class="btn" name="new" value="${ _("new")}">
                                    </form>
                                    <form style="padding:0px;margin:0px;" action=${ searchSpeakersURL } method="POST">
                                        <input type="submit" class="btn" name="search" value="${ _("search")}">
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