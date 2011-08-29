<% from MaKaC.common import Config %>
% if origin == "display":
<form action=${ postURL } enctype="multipart/form-data" method="POST" width="100%" onsubmit="return onsubmitDisplayActions();">
    <table width="100%" align="center">
% elif origin == "management":
<form action=${ postURL } enctype="multipart/form-data" method="POST" width="100%" onsubmit="return onsubmitManagementActions();">
    <table width="85%" align="left" style="padding: 5px 0 0 15px;">
% endif
        <input type="hidden" name="origin" value=${ origin }>
        % if errorList:
        <tr>
            <td>
                <table align="center" valign="middle" style="padding:10px; border:1px solid #5294CC; background:#F6F6F6">
                % for error in errorList:
                    <tr>
                        <td><span class="formError">${ error }</span></td>
                    </tr>
                % endfor
                </table>
            </td>
        </tr>
        % endif
        <tr>
            <td>
                <table width="100%" class="groupTable" align="center">
                    <tr>
                        <td class="groupTitle">${ _("Abstract")}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            <table align="center" width="100%">
                                <tr>
                                    <td align="right" valign="top" white-space="nowrap">
                                        <span class="dataCaptionFormat">${ _("Title")}</span>
                                        <span class="mandatoryField">*</span>
                                    </td>
                                    <td width="100%">
                                        <input id="abstractTitle" type="text" name="title" value=${ title } style="width:100%">
                                    </td>
                                </tr>
                                % for field in additionalFields:
                                    % if not field.isActive():
                                        <input type="hidden" name="f_${ field.getId() }" value="">
                                    % else:
                                        <tr>
                                            <td>&nbsp;</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"  style="white-space:nowrap">
                                                <span class="dataCaptionFormat">${ field.getCaption() }</span>&nbsp;${'<span class="mandatoryField">*</span>' if field.isMandatory() else ''}<br><br>
                                                <% nbRows = 10 %>
                                                % if field.getMaxLength() > 0:
                                                    % if field.getLimitation() == "words":
                                                        <% nbRows = int((int(field.getMaxLength())*4.5)/85) + 1 %>
                                                        <input type="hidden" name="maxwords${ field.getId().replace(" ", "_")}" value="${ field.getMaxLength() }">
                                                        <small><span id="maxLimitionCounter_${ field.getId().replace(" ", "_")}" style="padding-right:5px;">${ field.getMaxLength() } ${ _(" words left") }</span></small>
                                                    % else:
                                                        <% nbRows = int(int(field.getMaxLength())/85) + 1 %>
                                                        <input type="hidden" name="maxchars${ field.getId().replace(" ", "_")}" value="${ field.getMaxLength() }">
                                                        <small><span id="maxLimitionCounter_${ field.getId().replace(" ", "_")}" style="padding-right:5px;">${ field.getMaxLength() } ${ _(" chars left") }</span></small>
                                                    % endif
                                                % endif
                                                % if (nbRows > 30):
                                                    <% nbRows = 30 %>
                                                % endif
                                            </td>
                                            <td width="100%">
                                                % if field.getType() == "textarea":
                                                    <textarea id="f_${ field.getId() }" name="f_${ field.getId() }" width="100%" rows="${ nbRows }" style="width:100%">${ fieldsDict["f_"+ field.getId()] }</textarea>
                                                % elif field.getType() == "input":
                                                    <input id="f_${ field.getId() }" name="f_${ field.getId() }" value="${ fieldsDict["f_"+ field.getId()] }" style="width:100%">
                                                % endif
                                            </td>
                                        </tr>
                                    % endif
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
                            <table align="center" width="100%">
                                <textarea name="comments" rows="8" style="width:100%;">${ comments }</textarea>
                            </table>
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

function onsubmitManagementActions(data) {
    if (checkFields()) {
        setAuthorsParam(data);
        return true;
    } else {
        return false;
    }
    //setAuthorsParam(data);
    //return true;
}

function onsubmitDisplayActions(data) {
    if (checkFields() && hasPresenter()) {
        setAuthorsParam(data);
        return true;
    } else {
        if (authorsManager.getPrAuthors().getUsersList().length.get() != 0 && !hasPresenter()) {
            var popup = new AlertPopup($T('Submitting an abstract'), $T('You have to select at least one author as presenter.'));
            popup.open();
        }
        return false;
    }
    //setAuthorsParam(data);
    //return true;
}

% if attachedFilesAllowed:
// attached files
var initialFiles = ${ attachments };
var attachedFilesManager = new AbstractFilesManager($E('inPlaceMaterial'), $E('inPlaceExistingMaterial'), $E('uploadFileLink'), $E('sizeError'), initialFiles);
% endif

// authors
var initialPrAuthors = ${ jsonEncode(prAuthors) };
var initialCoAuthors = ${ jsonEncode(coAuthors) };

// manage both lists of authors.
var authorsManager = new AuthorsManager(initialPrAuthors, initialCoAuthors);

function setAuthorsParam(data) {
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
            limitedFieldManagerList.push(new WordsManager($E(limitedFieldList[i][0]), limitedFieldList[i][1], $E(limitedFieldList[i][2]), isMandatory));
        } else {
            limitedFieldManagerList.push(new CharsManager($E(limitedFieldList[i][0]), limitedFieldList[i][1], $E(limitedFieldList[i][2]), isMandatory));
        }
    }
}

// Add the mandatory fields to the parameter manager
function addPMToMandatoryFields() {
    for (var i=0; i<mandatoryFieldList.length; i++) {
        pmMandatoryFields.add($E(mandatoryFieldList[i]), null, false);
    }
}

//Check limited fields, mandatory fields, primary author and presenter
function checkFields() {
    // restart track table class name if needed
    var condLimited = checkLimitedFields();
    var condMandatory = pmMandatoryFields.check();
    var filesSize = attachedFilesManager.checkTotalFilesSize();
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

// Drag and drop for the authors
$('#sortspace').tablesorter({

    onDropFail: function() {
        var popup = new AlertPopup($T('Warning'), $T('You cannot move the author to this list because there is already an author with the same email address.'));
        popup.open();
    },
    canDrop: function(sortable, element) {
        if (sortable.attr('id') == 'inPlacePrAuthors') {
            return authorsManager.canDropElement('pr', element.attr('id'));
        } else if (sortable.attr('id') == 'inPlaceCoAuthors') {
            return authorsManager.canDropElement('co', element.attr('id'));
        }
        return false;
    },
    onUpdate: function() {
        authorsManager.updatePositions();
        authorsManager.checkPrAuthorsList();
        return;
    },
    sortables: '.sortblock ul', // relative to element
    sortableElements: '> li', // relative to sortable
    handle: '.authorTable', // relative to sortable element - the handle to start sorting
    placeholderHTML: '<li></li>' // the html to put inside the placeholder element
});

</script>
