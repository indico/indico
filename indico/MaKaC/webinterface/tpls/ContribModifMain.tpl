<table width="90%" border="0">
    ${ withdrawnNotice }
    <tr>
        <td>
            <table width="100%" align="left" border="0">
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
                    <td bgcolor="white" class="blacktext title"><b>${ title }</b></td>
                    <form action="${ dataModificationURL }" method="POST">
                    <td rowspan="${ rowspan }" valign="bottom" align="right" width="1%">
                        <input type="submit" class="btn" value="${ _("modify")}">
                    </td>
                    </form>
                </tr>
                % if self_._rh._target.getConference().getAbstractMgr().isActive() and self_._rh._target.getConference().hasEnabledSection("cfa") and self_._rh._target.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
                    % for f in additionalFields:
                        <tr>
                            <td class="dataCaptionTD" valign="top"><span class="dataCaptionFormat">${f.getCaption() | escape}</span></td>
                            <td bgcolor="white" valign="top">
                                <div class="md-preview-wrapper display">
                                    ${contrib.getField(f.getId()) | m}
                                </div>
                            </td>
                        </tr>
                    % endfor
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
                % endif
                <tr>
                    <td width="100%" colspan="3">
                        <div id="sortspace" width="100%">
                            <table width="100%">
                                % if eventType == "conference":
                                <tr>
                                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Primary authors")}</span></td>
                                    <td colspan="2">
                                        <table width="100%">
                                            <tr>
                                                <td style="width: 79%">
                                                    <div data-id="prAuthorsDiv" class="sortblock" style="width:100%">
                                                        <ul id="inPlacePrimaryAuthors" class="UIAuthorList" data-mode-copy="['inPlaceSpeakers']"></ul>
                                                    </div>
                                                </td>
                                                <td nowrap valign="top" style="width: 21%; text-align:right; padding-top:5px; padding-bottom:5px;">
                                                    <span id="inPlacePrimaryAuthorsMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                                                        <a class="dropDownMenu fakeLink" >${ _("Add primary author")}</a>
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
                                                <td style="width: 79%">
                                                    <div data-id="coAuthorsDiv" class="sortblock" style="width:100%">
                                                        <ul id="inPlaceCoAuthors" class="UIAuthorList"  data-mode-copy="['inPlaceSpeakers']"></ul>
                                                    </div>
                                                </td>
                                                <td nowrap valign="top" style="width: 21%; text-align:right; padding-top:5px; padding-bottom:5px;">
                                                    <span id="inPlaceCoAuthorsMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                                                        <a class="dropDownMenu fakeLink">${ _("Add co-author")}</a>
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
                                                <td style="width: 79%">
                                                    <div data-id="prAuthorsDiv" class="sortblock" style="width:100%">
                                                        <ul id="inPlaceSpeakers" class="UIAuthorList"  data-mode-copy="['inPlacePrimaryAuthors', 'inPlaceCoAuthors']"></ul>
                                                    </div>
                                                </td>
                                                <td nowrap valign="top" style="width: 21%; text-align:right; padding-top:5px; padding-bottom:5px;">
                                                    <span id="inPlaceSpeakersMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                                                        <a class="dropDownMenu fakeLink">${ _("Add presenter") if eventType == "conference" else  _("Add speakers")}</a>
                                                    </span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                % if Config.getInstance().getReportNumberSystems():
                <tr>
                    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Report numbers")}</span</td>
                    <td bgcolor="white" colspan="2">${ reportNumbersTable }</td>
                </tr>
                <tr>
                    <td colspan="3" class="horizontalLine">&nbsp;</td>
                </tr>
                % endif
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
var confId = '${ self_._rh._target.getConference().getId() }';
var methods = {'addNew': 'contribution.participants.addNewParticipant',
               'addExisting': 'contribution.participants.addExistingParticipant',
               'remove': 'contribution.participants.removeParticipant',
               'edit': 'contribution.participants.editParticipantData',
               'sendEmail': 'contribution.participants.sendEmailData',
               'changeSubmission': 'contribution.participants.changeSubmissionRights'};
% if eventType == "conference":
    //(confId, params, inPlaceListElem, inPlaceMenu, kindOfUser, userCaption, eventType, elementClass, initialList)
    var primaryAuthorManager = new ParticipantsListManager(confId, methods,
        {confId: confId, contribId: '${ id }', kindOfList: "prAuthor"}, $E('inPlacePrimaryAuthors'), $E('inPlacePrimaryAuthorsMenu'),
        "prAuthor", "primary author", "conference", "UIAuthorMove", ${primaryAuthors | n,j});
    $('#inPlacePrimaryAuthors').data('manager', primaryAuthorManager);

    var coAuthorManager = new ParticipantsListManager(confId, methods,
        {confId: confId, contribId: '${ id }', kindOfList: "coAuthor"}, $E('inPlaceCoAuthors'), $E('inPlaceCoAuthorsMenu'),
        "coAuthor", "co-author", "conference", "UIAuthorMove", ${coAuthors | n,j});
    $('#inPlaceCoAuthors').data('manager', coAuthorManager);

% endif:
    var speakerManager = new ParticipantsListManager(confId, methods,
        {confId: confId, contribId: '${ id }', kindOfList: "speaker"}, $E('inPlaceSpeakers'), $E('inPlaceSpeakersMenu'),
        "speaker", "speaker", "${eventType}", "UIAuthorMove", ${speakers | n,j});
    $('#inPlaceSpeakers').data('manager', speakerManager);

//Drag and drop for the authors
$('#sortspace').tablesorter({

    onDropFail: function() {
        var popup = new AlertPopup($T('Warning'), $T('You cannot move the user to this list because there is already an author with the same email address.'));
        popup.open();
    },

    canDrop: function(sortable, element) {
        if (sortable.attr('id') == 'inPlacePrimaryAuthors') {
            return primaryAuthorManager.canDrop(element.data('user').email) && (!element.parent('#inPlaceSpeakers').length || coAuthorManager.canDrop(element.data('user').email));
        } else if (sortable.attr('id') == 'inPlaceCoAuthors') {
            return coAuthorManager.canDrop(element.data('user').email) && (!element.parent('#inPlaceSpeakers').length || primaryAuthorManager.canDrop(element.data('user').email));
        } else if (sortable.attr('id') == 'inPlaceSpeakers') {
            return speakerManager.canDrop(element.data('user').email);
        }
        return false;
    },

    onReceive: function(ui) {
        var self = this;
        indicoRequest(
                'contribution.participants.updateAuthorList',
                {confId: confId, contribId: '${ id }',
                 from: ui.sender.attr('id'),
                 to: $(this).attr('id'),
                 item: ui.item.data('user').id,
                 index: ui.item.index()},
                function(result, error) {
                    if (!error) {
                        if ($(self).attr('id') != 'inPlaceSpeakers' && ui.sender.attr('id') != 'inPlaceSpeakers') {
                            ui.sender.data('manager').removeAuthorById(ui.item.data('user').id);
                        }
                        $(self).data('manager').usersList.insert(ui.item.data('user'), ui.item.index());
                        // we need to redraw in order to update the observers (menu more, edit, delete)
                        // otherwise the copy (in case of copying from authors to speakers) will not work
                        primaryAuthorManager.drawUserList();
                        coAuthorManager.drawUserList();
                        speakerManager.drawUserList();
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
        );
        return;
    },
    onReorder: function(ui) {
        var self = this;
        indicoRequest(
                'contribution.participants.reorderAuthorList',
                {confId: confId, contribId: '${ id }',
                 list: $(self).attr('id'),
                 item: ui.item.data('user').id,
                 index: ui.item.index()},
                function(result, error) {
                    if (!error) {
                        // Nothing to do
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
        );
        return;
    },
    sortables: '.sortblock ul', // relative to element
    sortableElements: '> li', // relative to sortable
    handle: '.authorMove', // relative to sortable element - the handle to start sorting
    placeholderHTML: '<li></li>' // the html to put inside the placeholder element
});

</script>



