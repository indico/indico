
<table border="0" width="90%" cellspacing="0" cellpadding="0" align="center">
    <tr>
        <td>
            <table width="100%">
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Abstract ID")}</span></td>
                    <td bgcolor="white">${ abstractId }</td>
                    <td align="right">
                        <table border="0" cellspacing="0" cellpadding="0">
                            <tr>
                                <td bgcolor="white" align="right" width="10">
                                    <a href=${ abstractXML } target="_blank"><img src=${ xmlIconURL } alt="${ _("print the current abstract")}" border="0"> </a>
                                </td>
                                <td bgcolor="white" align="right" width="10">
                                    <a href=${ abstractPDF } target="_blank"><img src=${ printIconURL } alt="${ _("print the current abstract")}" border="0"> </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Title")}</span></td>
                    <td bgcolor="white" width="100%">
                        <b>${ title }</b>
                    </td>
                    <td>&nbsp;</td>
                </tr>
                ${ additionalFields }
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Primary authors")}</span></td>
                    <td bgcolor="white" valign="top">${ primary_authors }</td>
                    <td>&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Co-authors")}</span></td>
                    <td bgcolor="white" valign="top">${ co_authors }</td>
                    <td>&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Presenters")}</span></td>
                    <td bgcolor="white" valign="top"><i>${ speakers }</i></td>
                    <td>&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Contribution type")}</span></td>
                    <td bgcolor="white" valign="top">${ type }</td>
                    <form action=${ modDataURL } method="POST">
                    <td align="right" valign="bottom">
                        <input type="submit" class="btn" name="modify" value="${ _("modify") }">
                    </td>
                    </form>
                </tr>
                <tr>
                    <td colspan="4" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Track classification")}</span></td>
                    <td bgcolor="white" valign="top" colspan="3">
                        <table width="100%">
                            <tr>
                                <td nowrap width="100%">${ tracks }</td>
                                <td align="right" valign="bottom">
                                    <table width="100%">
                                        <tr>
                                            <form action=${ changeTrackURL } method="POST">
                                            <td align="right" valign="bottom">
                                                <input type="submit" class="btn" value="${ _("change track assignment")}" ${ disable }>
                                            </td>
                                            </form>
                                        </tr>
                                        <tr>
                                            <form action=${ viewTrackDetailsURL } method="POST">
                                            <td align="right" valign="bottom">
                                                <input type="submit" class="btn" value="${ _("view details")}">
                                            </td>
                                            </form>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td colspan="4" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Status")}</span></td>
                    <td bgcolor="white" valign="top">${ status }</td>
                    <form action=${ backToSubmittedURL } method="POST">
                    <td bgcolor="white" valign="bottom" align="right" colspan="2">${'<input type="submit" class="btn" value="'+ _("back to submitted")+'">' if showBackToSubmitted else ""}</td>
                    </form>
                </tr>
                <tr>
                    <td class="dataCaptionTD" nowrap><span class="dataCaptionFormat">${ inlineContextHelp(_('Average of all the answers given by the reviewers for this abstract.')) }${ _("Average rating") }</span></td>
                    <td bgcolor="white" valign="top" colspan="3">${ rating }
                        % if rating != "":
                            ${ _(" (in ") + str(scaleLower) + _(" to ") + str(scaleHigher) + _(" scale) ") }
                        % else:
                            ${ _("No rating yet") }
                        % endif
                    </td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Submitted by")}</span></td>
                    <form action=${ changeSubmitterURL } method="POST">
                    <td>${ submitter }</td>
                    <td bgcolor="white" valign="bottom" align="right" colspan="2"><input type="submit" class="btn" value="${ _("change submitter")}"></td>
                    </form>
                </tr>
                <tr>
                    <td colspan="4" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Submitted on")}</span></td>
                    <td bgcolor="white" valign="top" colspan="3">${ submitDate }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Last modified on")}</span></td>
                    <td bgcolor="white" valign="top" colspan="3">${ modificationDate }</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Comments")}</span></td>
                    <td bgcolor="white" valign="top" colspan="3"><pre>${ comments }</pre></td>
                </tr>
                ${ mergeFrom }
                <tr>
                    <td colspan="4" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Contribution")}</span></td>
                    <td bgcolor="white" valign="top" colspan="3">${ contribution }</td>
                </tr>
                <tr>
                    <td align="center" colspan="3" style="border-top: 2px solid #777777">
                        <table align="center" border="0">
                            <tr>
                                <td>
                                    <form action=${ acceptURL } method="POST">
                                        <input type="submit" class="btn" value="${ _("accept")}" ${ disable }>
                                    </form>
                                </td>
                                <td>
                                    <form action=${ rejectURL } method="POST">
                                        <input type="submit" class="btn" value="${ _("reject")}" ${ disable }>
                                    </form>
                                </td>
                                <td>
                                    <form action=${ duplicateURL } method="POST">
                                        <input type="submit" class="btn" value="${ duplicatedButton }" ${ dupDisable }>
                                    </form>
                                </td>
                                <td>
                                    <form action=${ mergeIntoURL } method="POST">
                                        <input type="submit" class="btn" value="${ mergeButton }" ${ mergeDisable }>
                                    </form>
                                </td>
                                <td>
                                    <form action=${ propToAccURL } method="POST">
                                        <input type="submit" class="btn" value="${ _("propose to accept")}" ${ disable }>
                                    </form>
                                </td>
                                <td>
                                    <form action=${ propToRejURL } method="POST">
                                        <input type="submit" class="btn" value="${ _("propose to reject")}" ${ disable }>
                                    </form>
                                </td>
                                <td>
                                    <form action=${ withdrawURL } method="POST">
                                        <input type="submit" class="btn" value="${ _("withdraw")}"${ disableWithdraw }>
                                    </form>
                                </td>
                            </tr>
                        </table>
                        <br>
                    </td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td>
            <table align="center" border="0">
                <tr>
                    <td>
                        <form action=${ abstractListURL } method="POST">
                            <input type="submit" class="btn" value="&lt;&lt;${ _("back to the abstract list")}">
                        </form>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
