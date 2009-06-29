
<table border="0" width="90%%" cellspacing="0" cellpadding="0">
    <tr>
        <td>
            <table width="100%%" align="left" border="0" style="border-right:1px solid #777777">
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Abstract ID")%></span></td>
                    <td bgcolor="white">%(abstractId)s</td>
                    <td align="right">
                        <table border="0" cellspacing="0" cellpadding="0">
                            <tr>
                                <td bgcolor="white" align="right" width="10">
                                    <a href=%(abstractXML)s target="_blank"><img src=%(xmlIconURL)s alt="<%= _("print the current abstract")%>" border="0"> </a>
                                </td>
                                <td bgcolor="white" align="right" width="10">
                                    <a href=%(abstractPDF)s target="_blank"><img src=%(printIconURL)s alt="<%= _("print the current abstract")%>" border="0"> </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
                    <td bgcolor="white" width="100%%">
                        <b>%(title)s</b>
                    </td>
                    <td>&nbsp;</td>
                </tr>
                %(additionalFields)s 
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Primary authors")%></span></td>
                    <td bgcolor="white" valign="top">%(primary_authors)s</td>
                    <td>&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Co-authors")%></span></td>
                    <td bgcolor="white" valign="top">%(co_authors)s</td>
                    <td>&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Presenters")%></span></td>
                    <td bgcolor="white" valign="top"><i>%(speakers)s</i></td>
                    <td>&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Contribution type")%></span></td>
                    <td bgcolor="white" valign="top">%(type)s</td>
                    <form action=%(modDataURL)s method="POST">
                    <td align="right" valign="bottom">
                        <input type="submit" class="btn" name="modify" value="<%= _("modify") %>">
                    </td>
                    </form>
                </tr>
                <tr>
                    <td colspan="4" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Track classification")%></span></td>
                    <td bgcolor="white" valign="top" colspan="3">
                        <table width="100%%">
                            <tr>
                                <td nowrap width="100%%">%(tracks)s</td>
                                <td align="right" valign="bottom">
                                    <table width="100%%">
                                        <tr>
                                            <form action=%(changeTrackURL)s method="POST">
                                            <td align="right" valign="bottom">
                                                <input type="submit" class="btn" value="<%= _("change track assignment")%>" %(disable)s>
                                            </td>
                                            </form>
                                        </tr>
                                        <tr>
                                            <form action=%(viewTrackDetailsURL)s method="POST">
                                            <td align="right" valign="bottom">
                                                <input type="submit" class="btn" value="<%= _("view details")%>">
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
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Status")%></span></td>
                    <td bgcolor="white" valign="top">%(status)s</td>
                    <form action=%(backToSubmittedURL)s method="POST">
                    <td bgcolor="white" valign="bottom" align="right" colspan="2"><% if showBackToSubmitted:%><input type="submit" class="btn" value="<%= _("back to submitted")%>"><% end %></td>
                    </form>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Submitted by")%></span></td>
                    <form action=%(changeSubmitterURL)s method="POST">
                    <td>%(submitter)s</td>
                    <td bgcolor="white" valign="bottom" align="right" colspan="2"><input type="submit" class="btn" value="<%= _("change")%>"></td>
                    </form>
                </tr>
                <tr>
                    <td colspan="4" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Submitted on")%></span></td>
                    <td bgcolor="white" valign="top" colspan="3">%(submitDate)s</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Last modified on")%></span></td>
                    <td bgcolor="white" valign="top" colspan="3">%(modificationDate)s</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Comments")%></span></td>
                    <td bgcolor="white" valign="top" colspan="3"><pre>%(comments)s</pre></td>
                </tr>
                %(mergeFrom)s
                <tr>
                    <td colspan="4" class="horizontalLine">&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Contribution")%></span></td>
                    <td bgcolor="white" valign="top" colspan="3">%(contribution)s</td>
                </tr>
                <tr>
                    <td align="center" colspan="3" style="border-top: 2px solid #777777">
                        <table align="center" border="0">
                            <tr>
                                <td>
                                    <form action=%(acceptURL)s method="POST">
                                        <input type="submit" class="btn" value="<%= _("accept")%>" %(disable)s>
                                    </form>
                                </td>
                                <td>
                                    <form action=%(rejectURL)s method="POST">
                                        <input type="submit" class="btn" value="<%= _("reject")%>" %(disable)s>
                                    </form>
                                </td>
                                <td>
                                    <form action=%(duplicateURL)s method="POST">
                                        <input type="submit" class="btn" value="%(duplicatedButton)s" %(dupDisable)s>
                                    </form>
                                </td>
                                <td>
                                    <form action=%(mergeIntoURL)s method="POST">
                                        <input type="submit" class="btn" value="%(mergeButton)s" %(mergeDisable)s>
                                    </form>
                                </td>
                                <td>
                                    <form action=%(propToAccURL)s method="POST">
                                        <input type="submit" class="btn" value="<%= _("propose to accept")%>" %(disable)s>
                                    </form>
                                </td>
                                <td>
                                    <form action=%(propToRejURL)s method="POST">
                                        <input type="submit" class="btn" value="<%= _("propose to reject")%>" %(disable)s>
                                    </form>
                                </td>
                                <td>
                                    <form action=%(withdrawURL)s method="POST">
                                        <input type="submit" class="btn" value="<%= _("withdraw")%>"%(disableWithdraw)s>
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
                        <form action=%(abstractListURL)s method="POST">
                            <input type="submit" class="btn" value="&lt;&lt;<%= _("back to the abstract list")%>">
                        </form>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
