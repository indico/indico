<table width="90%" border="0" style="border-right:1px solid #777777">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Abstract ID")}</td>
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
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Title")}</span></td>
                    <td bgcolor="white" width="90%">
                        <table width="100%"><tr>
                            <td><b>${ title }</b></td>
                        </tr></table>
                    </td>
                </tr>
                ${ additionalFields }
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Primary authors")}</span></td>
                    <td bgcolor="white" valign="top">${ primary_authors }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Co-authors")}</span></td>
                    <td bgcolor="white" valign="top">${ co_authors }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Presenters")}</span></td>
                    <td bgcolor="white" valign="top"><i>${ speakers }</i></td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Contribution type")}</span></td>
                    <td bgcolor="white" valign="top">${ type }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Track classification")}</span></td>
                    <td bgcolor="white" valign="top">${ tracks }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Attached files")}</span></td>
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
                    <td bgcolor="white" valign="top">
                        ${lastJudgement if lastJudgement else _("No proposition yet")}
                        <br>
                        ${lastJudgementComment if lastJudgementComment else ""}
                    </td>
                    <td align="right" valign="top" rowspan="3">
                        <table align="right">
                            <tr>
                                <form action=${ proposeToAccURL } method="POST">
                                <td align="right">
                                        ${ proposeToAcceptButton }
                                </td>
                                </form>
                            </tr>
                            <tr>
                                <form action=${ proposeToRejURL } method="POST">
                                <td align="right">
                                        ${ proposeToRejectButton }
                                </td>
                                </form>
                            </tr>
                            <tr>
                                <form action=${ proposeForOtherTracksURL } method="POST">
                                <td align="right">
                                        ${ proposeForOtherTracksButton }
                                </td>
                                </form>
                            </tr>
                            <tr>
                                <form action=${ duplicatedURL } method="POST">
                                <td align="right">
                                        ${ duplicatedButton }
                                </td>
                                </form>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Status")}</span></td>
                    <td width="100%" valign="top">${ statusDetails } <br> ${ statusComment }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Your rating for this abstract") }</span></td>
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
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Submitted by")}</span></td>
                    <td bgcolor="white" valign="top">${ submitter }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Submitted on")}</span></td>
                    <td bgcolor="white" valign="top">${ submissionDate }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Last modified on")}</span></td>
                    <td bgcolor="white" valign="top">${ modificationDate }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Comments")}</span></td>
                    <td bgcolor="white" valign="top"><pre>${ comments }</pre></td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Contribution")}</span></td>
                    <td bgcolor="white" valign="top" colspan="3"><pre>${ contribution }</pre></td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>
