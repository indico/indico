<table width="90%" border="0">
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Abstract ID")}</span>
        </td>
        <td bgcolor="white">${ abstractId }</td>
        <td align="right">
            <table border="0" cellspacing="1" cellpadding="0">
                <tr>
                    <td align="right">
                        <a href=${ abstractPDF } target="_blank"><img src=${ printIconURL } alt="${ _("print the current abstract")}" border="0"> </a>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD" >
            <span class="dataCaptionFormat"> ${ _("Title")}</span>
        </td>
        <td bgcolor="white" width="90%">
            <table width="100%">
                <tr>
                    <td><b>${ title }</b></td>
                </tr>
            </table>
        </td>
    </tr>

    % for caption, field in additionalFields:
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat">${caption}</span></td>
            <td bgcolor="white">${field | m}</td>
        </tr>
    % endfor

    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Primary authors")}</span>
        </td>
        <td bgcolor="white" valign="top">${ primary_authors }</td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Co-authors")}</span>
        </td>
        <td bgcolor="white" valign="top">${ co_authors }</td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Presenters")}</span>
        </td>
        <td bgcolor="white" valign="top"><i>${ speakers }</i></td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Contribution type")}</span>
        </td>
        <td bgcolor="white" valign="top">${ type }</td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Track classification")}</span>
        </td>
        <td bgcolor="white" valign="top">${ tracks }</td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Attached files")}</span>
        </td>
        <td bgcolor="white" valign="top">
            % for file in attachments:
                <div style="padding-bottom:3px;"><a href=${ file["url"] }>${ file["file"]["fileName"] }</a></div>
            % endfor
        </td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Your last proposition") }</span></td>
    <td>
        <span>${lastJudgement if lastJudgement else _("No proposition yet")}</span>
        <p class="quotation pre">${lastJudgementComment if lastJudgementComment else ""}</p>
    </td>
    <td rowspan="3">
        <table>
            % if showAcceptButton:
            <tr>

                <td>
                    <form action=${ acceptURL } method="POST">
                        <input type="submit" class="btn" value="${_("accept")}" style="width:205px" ${ buttonsStatus }>
                    </form>
                </td>
            </tr>
            <tr>
                <td>
                    <form action=${ rejectURL } method="POST">
                        <input type="submit" class="btn" value="${_("reject")}" style="width:205px" ${ buttonsStatus }>
                    </form>
                </td>
            % endif
            <tr>
            <tr>
                <td>
                    <form action=${ proposeToAccURL } method="POST">
                        <input type="submit" class="btn" value="${_("propose to be accepted")}" style="width:205px" ${ buttonsStatus }>
                    </form>
                </td>
            </tr>
            <tr>
                <td>
                    <form action=${ proposeToRejURL } method="POST">
                        <input type="submit" class="btn" value="${_("propose to be rejected")}" style="width:205px" ${ buttonsStatus }>
                    </form>
                </td>
            </tr>
            <tr>
                <td>
                    <form action=${ proposeForOtherTracksURL } method="POST">
                        <input type="submit" class="btn" value="${_("propose for other tracks")}" style="width:205px" ${ buttonsStatus }>
                    </form>
                </td>
            </tr>
            % if showDuplicated:
            <tr>
                <td>
                    <form action=${ duplicatedURL } method="POST">
                        % if isDuplicated:
                            <input type="submit" class="btn" value="${_("unmark as duplicated")}" style="width:205px" ${ buttonsStatus }>
                        % else:
                            <input type="submit" class="btn" value="${_("mark as duplicated")}" style="width:205px"  ${ buttonsStatus }>
                        % endif
                    </form>
                </td>
            </tr>
            % endif
        </table>
    </td>
</tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Status")}</span>
        </td>
        <td colspan="2" valign="top">
            <table width="100%">
                <tr>
                    <td width="100%">${ statusDetails }</td>
                </tr>
                <tr>
                    <td colspan="2">${ statusComment }</td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD" >
            <span class="dataCaptionFormat"> ${ _("Your rating for this abstract") }</span>
        </td>
        <td bgcolor="white" valign="top">${ rating }
            % if rating != "":
                ${ _(" (in ") + str(scaleLower) + _(" to ") + str(scaleHigher) + _(" scale) ") }
            % else:
            ${ _("No rating yet") }
            % endif
        </td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Submitted by")}</span>
        </td>
        <td bgcolor="white" valign="top">${ submitter }</td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Submitted on")}</span>
        </td>
        <td bgcolor="white" valign="top">${ submissionDate }</td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Last modified on")}</span>
        </td>
        <td bgcolor="white" valign="top">${ modificationDate }</td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Comments")}</span>
        </td>
        <td bgcolor="white" valign="top"><pre>${ comments }</pre></td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD" >
            <span class="dataCaptionFormat"> ${ _("Contribution")}</span>
        </td>
        <td bgcolor="white" valign="top" colspan="2"><pre>${ contribution }</pre></td>
    </tr>
    <tr>
        <td colspan="3" style="border-bottom: 2px solid #AAAAAA">&nbsp;</td>
    </tr>
</table>
