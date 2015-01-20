<table border="0" width="90%" cellspacing="0" cellpadding="0" align="center">
    % if abstractAccepted:
    <tr>
        <td align="center">
            <div style="padding: 10px; margin: 10px; border: 1px solid #DDD; font-size: 14px; color: #881122">
                ${ _("You cannot modify this abstract because it has already been accepted. In order to change the information that is displayed in the Book of Abstracts and timetable you should edit the corresponding contribution (%s) directly.") % contribution}
            </div>
        </td>
    </tr>
    % endif
    <tr>
        <td>
            <table width="100%">
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Abstract ID")}</span></td>
                    <td bgcolor="white">${ abstract.getId() }</td>
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
                        <b>${ abstract.getTitle() }</b>
                    </td>
                    <td>&nbsp;</td>
                </tr>
                % for f in additionalFields:
                    <tr>
                        <td class="dataCaptionTD" valign="top"><span class="dataCaptionFormat">${f.getCaption() | escape}</span></td>
                        <td bgcolor="white" valign="top">
                            <div class="md-preview-wrapper display">
                                ${abstract.getField(f.getId()) | m}
                            </div>
                        </td>
                    </tr>
                % endfor
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
                    <td>&nbsp;</td>
                </tr>
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Attached files")}</span></td>
                    <td bgcolor="white" valign="top">
                        % for file in attachments:
                            <div style="padding-bottom:3px;"><a href=${ file["url"] }>${ file["file"]["fileName"] }</a></div>
                        % endfor
                    </td>
                    <form action=${ modDataURL } method="POST">
                    <td align="right" valign="bottom">
                        <input type="submit" class="btn" name="modify" value="${ _("modify") }" ${"disabled" if abstractAccepted else ""}>
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
                    <td bgcolor="white" valign="bottom" align="right" colspan="2">
                        % if showBackToSubmitted:
                            <input type="submit" id="backToSubmitted" class="btn" value="${_("back to submitted")}">
                        % endif
                    </td>
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
                    <td>
                        <div id="submitterPlace">
                            <a href="mailto:${ submitterEmail }?subject=[${ confTitle }] ${ _("Abstract") } ${ abstractId }: ${ abstract.getTitle() }">${ submitterFullName } (${ submitterAffiliation })</a>
                        </div>
                    </td>
                    <td bgcolor="white" valign="bottom" align="right" colspan="2"><input type="button" value="${ _("change submitter")}" id="changeSubmitter" ${"disabled" if abstractAccepted else ""}></td>
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

<script>

var status = '${ statusName }';

$("#backToSubmitted").click(function(){
    if (status=="ACCEPTED") {
        var content = $("<div/>").css("width", "380px");
        content.append($("<div/>").css("margin-bottom", "10px").append($T("The contribution associated with this abstract and all the existing sub-contributions within it will be ")).append($("<span/>").css("font-weight", "bold").append($T("deleted."))));
        content.append($("<div/>").css("margin-bottom", "10px").append($T("The abstract will remain and its status will change to ")).append($("<span/>").css("font-weight", "bold").append($T("submitted."))));
        content.append($T("Do you want to continue?"));
        var popup = new ConfirmPopup($T("Back to submitted status"), content,
                function(action) {
                    if (action) {
                        window.location = ${ backToSubmittedURL };
                    }
                }, $T("Confirm"));
        popup.open();
    } else {
        window.location = ${ backToSubmittedURL };
    }
});

var changeSubmitterHandler = function(user) {
	indicoRequest(
            'abstracts.changeSubmitter',
            {
                confId: '${ confId }',
                submitterId: user['0']['id'],
                abstractId: '${ abstractId }'
            },
            function(result,error) {
                if (!error) {
                    // update the submitter
                    var link = Html.a({href: 'mailto:'+result['email']+'?subject=['+'${escapeHTMLForJS(confTitle)}'+'] '+$T("Abstract ")+'${ abstractId }'+': '+'${escapeHTMLForJS(abstract.getTitle())}'},
                                      result['name']+' ('+result['affiliation']+')');
                    $E('submitterPlace').set(link);
                } else {
                    IndicoUtil.errorReport(error);
                }
            }
    );
};

$("#changeSubmitter").click(function(){
    // params: (title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
    //         showToggleFavouriteButtons, chooseProcess)
    var chooseUsersPopup = new ChooseUsersPopup($T("Change submitter"), true, '${ confId }', false,
            true, true, true, true, false, changeSubmitterHandler);
    chooseUsersPopup.execute();
});

</script>
