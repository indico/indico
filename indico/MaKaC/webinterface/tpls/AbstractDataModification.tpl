<%inherit file="ConfDisplayBodyBase.tpl"/>
<% from MaKaC.common import Config %>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">

<%include file="MarkdownMathJaxHelp.tpl"/>

% if origin == "display":
<form action=${ postURL } enctype="multipart/form-data" method="POST" width="100%" onsubmit="return onsubmitDisplayActions();">
    <table width="100%" align="center">
% elif origin == "management":
<form action=${ postURL } enctype="multipart/form-data" method="POST" width="100%" onsubmit="return onsubmitManagementActions();">
    <table width="85%" align="left" style="padding: 5px 0 0 15px;">
% endif

        <input type="hidden" name="origin" value=${ origin }>
        <tr>
            <td>
                <table class="groupTable">
                    <tr>
                        <td class="groupTitle">${ _("Abstract")}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            <table id="abstract-field-table" style="min-width: 800px;">
                                <tr>
                                    <td align="right" valign="top" white-space="nowrap">
                                        <span class="dataCaptionFormat">${ _("Title")}</span>
                                        <span class="mandatoryField title">*</span>
                                    </td>
                                    <td>
                                        <input id="abstractTitle" type="text" name="title" value=${abstractTitle} style="width:100%">
                                    </td>
                                </tr>
                                % for field in additionalFields:
                                    <%include file="AbstractField.tpl" args="field=field, fdict=fieldDict"/>
                                % endfor
                                <tr><td>&nbsp;</td></tr>
                                <tr>
                                    <td align="right" valign="top" style="white-space:nowrap;">
                                        <span class="dataCaptionFormat">${ _("Presentation type") }</span>&nbsp;
                                    </td>
                                    <td>
                                        <select name="type">
                                            % if typeSelected == None:
                                                <option value="" selected>--${ _("not specified")}--</option>
                                            % else:
                                                <option value="">--${ _("not specified")}--</option>
                                            % endif
                                            % for contribType in types:
                                                % if typeSelected == None:
                                                    <option value=${ contribType.getId() }>${ contribType.getName() }</option>
                                                % else:
                                                    <option value=${ contribType.getId() } ${ "selected" if contribType.getId() == typeSelected.getId() else "" }>${ contribType.getName() }</option>
                                                % endif
                                            % endfor
                                        </select>
                                    </td>
                            </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                </table>
            </td>
        </tr>
        % if attachedFilesAllowed:
        <tr>
            <td>
                <table align="center" width="100%" class="groupTable">
                    <tr>
                        <td class="groupTitle">${ _("Attached files")}</td>
                    </tr>
                    <tr>
                        <td>
                            <div id="inPlaceExistingMaterial" style="display:none;">
                                <div class="subGroupTitleAbstract">${ _("Files already attached to the abstract") }</div>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <div id="inPlaceMaterial"></div>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <span id="uploadFileLink" class="fakeLink" style="padding-left:6px; padding-top:6px;" onclick="attachedFilesManager.addElement();">${ _("Attach a file") }</span>
                            <span id="sizeError" class="formError" style="padding-left:6px; padding-top:6px; display:none;">${ _("Maximum size allowed (%sMB) has been exceeded") % (Config.getInstance().getMaxUploadFilesTotalSize()) }</span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td>&nbsp;</td>
        </tr>
        % endif
        <tr>
            <td width="100%">
                <div id="sortspace" width="100%">
                    <table align="center" width="100%" class="groupTable">
                        <tr>
                            <td class="groupTitle">${ _("Primary Authors")}</td>
                            <input type="hidden" name="prAuthors" id="prAuthors"></input>
                        </tr>
                        <tr id="prAuthorError" style="display:none">
                            <td class="authorError">${ _("You have to add at least one primary author.") }</td>
                        </tr>
                        <tr>
                            <td nowrap valign="top" class="addAuthorTD">
                                <span id="inPlacePrAuthorsMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                                    <a class="dropDownMenu fakeLink" onclick="authorsManager.getPrAuthors().addManagementMenu();">${ _("Add primary author") }</a>
                                </span>
                            </td>
                        </tr>
                    </table>
                    <div data-id="prAuthorsDiv" class="sortblock">
                        <ul id="inPlacePrAuthors"></ul>
                    </div>
                    <table align="center" width="100%" class="groupTable">
                        <tr>
                            <td class="groupTitle">${ _("Co-Authors")}</td>
                            <input type="hidden" name="coAuthors" id="coAuthors"></input>
                        </tr>
                        <tr>
                            <td nowrap valign="top" class="addAuthorTD">
                                <span id="inPlaceCoAuthorsMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                                    <a class="dropDownMenu fakeLink" onclick="authorsManager.getCoAuthors().addManagementMenu();">${ _("Add co-author") }</a>
                                </span>
                            </td>
                        </tr>
                    </table>
                    <div data-id="coAuthorsDiv" class="sortblock">
                        <ul id="inPlaceCoAuthors"></ul>
                    </div>
                </div>
            </td>
        </tr>
        <tr>
            <td>
                % if len(tracks):
                    <table align="center" width="95%" class="groupTable">
                        <tr>
                            <td class="groupTitle">${ _("Track classification")}&nbsp;${'<span class="mandatoryField">*</span>' if tracksMandatory else ''}</td>
                        </tr>
                        <tr>
                            <td>&nbsp;</td>
                        </tr>
                        <tr>
                            <td>
                                <table id="tracksTable" class="groupTable" align="center" width="80%" bgcolor="white" style="background:white;">
                                    % for track in tracks:
                                        <% checked = "" %>
                                        % if str(track.getId()) in tracksSelected:
                                            <% checked = "checked" %>
                                        % endif
                                        <tr>
                                            <td style="color:black; padding-bottom:5px;">
                                                % if trackListType == "checkbox":
                                                    % if tracksMandatory:
                                                        <input type="${ trackListType }" id="track_${ track.getId() }" value=${ track.getId() } name="tracks" onclick="removeCheckBoxError();" ${ checked }>
                                                    % else:
                                                        <input type="${ trackListType }" id="track_${ track.getId() }" value=${ track.getId() } name="tracks" ${ checked }>
                                                    % endif
                                                % elif trackListType == "radio":
                                                    % if tracksMandatory:
                                                        <input type="${ trackListType }" id="track_${ track.getId() }" value=${ track.getId() } name="tracks" ${ checked } onclick="removeCheckBoxError();">
                                                    % else:
                                                        <input type="${ trackListType }" id="track_${ track.getId() }" value=${ track.getId() } name="tracks" ${ checked }>
                                                    % endif
                                                % endif
                                                ${ track.getTitle() }
                                            </td>
                                        </tr>
                                        <tr>
                                            <td>
                                                <table width="80%" align="center">
                                                    <tr>
                                                        <td>${ track.getDescription() }</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    % endfor
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td>&nbsp;</td>
                        </tr>
                    </table>
                % endif
            </td>
        </tr>
        <tr>
            <td>
                <table align="center" width="95%" class="groupTable">
                    <tr>
                        <td class="groupTitle">${ _("Comments")}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td width="100%">
                                <textarea name="comments" rows="8" style="width:100%;">${ comments }</textarea>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr id="formError" style="display:none;">
            <td nowrap class="formError" style="padding-bottom:10px;">
                <span>${ _("The document contains errors, please revise it.") }</span>
            </td>
        </tr>
        <tr>
            <td align="center">
                <input type="submit" class="btn" name="validate" value="${ _("submit")}">
                <input type="submit" class="btn" name="cancel" value="${ _("cancel")}" onclick="this.form.onsubmit= function(){return true;};">
            </td>
        </tr>
    </table>
</form>

<script type="text/javascript">

function onsubmitManagementActions() {
    if (checkFields()) {
        setAuthorsParam();
        return true;
    } else {
        return false;
    }
}

function onsubmitDisplayActions() {
    if (checkFields() && ((hasPresenter() && ${jsonEncode(showSelectAsSpeaker)} && ${jsonEncode(isSelectSpeakerMandatory)}) || ${jsonEncode(not showSelectAsSpeaker)} || ( ${jsonEncode(showSelectAsSpeaker)} && ${jsonEncode(not isSelectSpeakerMandatory)} ))) {
        setAuthorsParam();
        return true;
    } else {
        if (authorsManager.getPrAuthors().getUsersList().length.get() != 0 && !hasPresenter() && ${jsonEncode(showSelectAsSpeaker)} && ${jsonEncode(isSelectSpeakerMandatory)} ) {
            var popup = new AlertPopup($T('Submitting an abstract'), $T('You have to select at least one author as presenter.'));
            popup.open();
        }
        return false;
    }
}

% if attachedFilesAllowed:
// attached files
var initialFiles = ${ attachments | n,j };
var attachedFilesManager = new AbstractFilesManager($E('inPlaceMaterial'), $E('inPlaceExistingMaterial'), $E('uploadFileLink'), $E('sizeError'), initialFiles);
% endif

// authors
var initialPrAuthors = ${ jsonEncode(prAuthors) };
var initialCoAuthors = ${ jsonEncode(coAuthors) };

// manage both lists of authors.
var authorsManager = new AuthorsManager(initialPrAuthors, initialCoAuthors, ${jsonEncode(showSelectAsSpeaker)});

function setAuthorsParam() {
    var usersList = authorsManager.getPrAuthors().getUsersList();
    if (usersList.length.get() == 0) {
        $E('prAuthors').set('[]');
    } else {
        $E('prAuthors').set(Json.write(usersList));
    }
    usersList = authorsManager.getCoAuthors().getUsersList();
    if (usersList.length.get() == 0) {
        $E('coAuthors').set('[]');
    } else {
        $E('coAuthors').set(Json.write(usersList));
    }
}

function hasPresenter() {
    if (authorsManager.getPrAuthors().hasPresenter())
        return true;
    else if (authorsManager.getCoAuthors().hasPresenter())
        return true;
    return false;
}


// limited and mandatory fields
var limitedFieldManagerList = [];
var limitedFieldList = ${ limitedFieldList };
var mandatoryFieldList = ${ mandatoryFieldList };
mandatoryFieldList.push("abstractTitle"); // append the title id which is in this template
var pmMandatoryFields = new IndicoUtil.parameterManager();

var checkTrackOptions = function() {
    /* Extra function to use in the parameter manager.
       Checks if at least one of the checkboxes/radiobuttons is checked.
    */
    if ($('input:checked[id^=track_]').length > 0) {
        return null;
    }else {
        return Html.span({}, $T("At least one must be selected"));
    }
};


// Add to parameter manager the kind of list for the track selection
% if trackListType == "checkbox" and tracksMandatory and len(tracks):
    pmMandatoryFields.add($E('tracksTable'), 'checkBoxList', true, checkTrackOptions);
% endif

% if trackListType == "radio" and tracksMandatory and len(tracks):
    pmMandatoryFields.add($E('tracksTable'), 'radio', true, checkTrackOptions);
% endif

// Remove the error of the track area when a new checkbox/radio button is selected
function removeCheckBoxError() {
    if ($E('tracksTable').dom.className.slice(-7) == "invalid") {
        $E('tracksTable').dom.className = "groupTable";
    }
}

// Manager of limited fields, create the appropiate manager for each case
function createLimitedFieldsMgr() {
    for (var i=0; i<limitedFieldList.length; i++) {
        var isMandatory = (limitedFieldList[i][4] == "True");
        if (limitedFieldList[i][3] == "words") {
            limitedFieldManagerList.push(new WordsManager($('[name="'+limitedFieldList[i][0]+'"]'), limitedFieldList[i][1], $E(limitedFieldList[i][2]), isMandatory));
        } else {
            limitedFieldManagerList.push(new CharsManager($('[name="'+limitedFieldList[i][0]+'"]'), limitedFieldList[i][1], $E(limitedFieldList[i][2]), isMandatory));
        }
    }
}

// Add the mandatory fields to the parameter manager
function addPMToMandatoryFields() {
    // Correct mandatoryFieldList ids with "wmd-input-" prefix to match Pagedown's textareas
    % for field in additionalFields:
        % if field.getType() == "textarea":
            var textarea_index = $.inArray('f_${ field.getId() }', mandatoryFieldList);
            if(textarea_index > -1){
                mandatoryFieldList[textarea_index] = "wmd-input-"+mandatoryFieldList[textarea_index];
            }
        % endif
    % endfor

    for (var i=0; i<mandatoryFieldList.length; i++) {
        pmMandatoryFields.add($E(mandatoryFieldList[i]), null, false);
    }
}

//Check limited fields, mandatory fields, primary author and presenter
function checkFields() {
    // restart track table class name if needed
    var condMandatory = pmMandatoryFields.check();
    var condLimited = checkLimitedFields();
% if attachedFilesAllowed:
    var filesSize = attachedFilesManager.checkTotalFilesSize();
% else:
    var filesSize = true;
% endif
% if tracksMandatory and len(tracks):
    // To avoid 'gr' case
    if ($E('tracksTable').dom.className == 'gr') {
        $E('tracksTable').dom.className = 'groupTable';
    } else if ($E('tracksTable').dom.className == 'gr invalid') {
        $E('tracksTable').dom.className = 'groupTable invalid';
    }
% endif
% if origin == "management":
    if (condLimited && condMandatory && filesSize) {
        $E('formError').dom.style.display = "none";
        return true;
    } else {
        $E('formError').dom.style.display = "";
        return false;
    }
% else:
    var prAuthorsLength = authorsManager.getPrAuthors().getUsersList().length.get();

    if (condLimited && condMandatory && prAuthorsLength && filesSize) {
        $E('formError').dom.style.display = "none";
        return true;
    } else {
        $E('formError').dom.style.display = "";
        if (prAuthorsLength == 0) {
            $E('prAuthorError').dom.style.display = '';
        }
        return false;
    }
% endif
}

// Check if every limited field content is valid
function checkLimitedFields() {
    var result = true;
    for (var i=0; i<limitedFieldManagerList.length; i++) {
        if (!limitedFieldManagerList[i].checkPM() || !limitedFieldManagerList[i].checkPMEmptyField()) {
            result = false;
        }
    }
    return result;
}

// On load
createLimitedFieldsMgr();
addPMToMandatoryFields();

</script>
</%block>