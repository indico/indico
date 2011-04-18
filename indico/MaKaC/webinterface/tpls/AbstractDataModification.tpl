
<form action=${ postURL } method="POST" width="100%" onsubmit="return checkFields();">
    <table width="100%" align="center">
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
                                ${ additionalFields }
                                ${ types }
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
           <td>
                <table align="center" width="100%" class="groupTable">
                    <tr>
                        <td class="groupTitle">${ _("Primary Authors")}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            <table cellspacing="1" align="center">
                                ${ primary_authors }
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td align="center">
                            <input type="submit" class="btn" name="add_primary_author" value="${ _("new primary author")}">
                            <input type="submit" class="btn" name="remove_primary_authors" value="${ _("remove selected primary authors")}">
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td>
                <table align="center" width="95%" class="groupTable">
                    <tr>
                        <td class="groupTitle">${ _("Co-Authors")}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            <table cellspacing="1" align="center">
                                ${ secondary_authors }
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td align="center">
                            <input type="submit" class="btn" name="add_secondary_author" value="${ _("new co-author")}">
                            <input type="submit" class="btn" name="remove_secondary_authors" value="${ _("remove selected co-authors")}">
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td>
                % if len(tracks):
                    <table align="center" width="95%" class="groupTable">
                        <tr>
                            <td class="groupTitle">${ _("Track classification")}&nbsp;${ tracksMandatory }</td>
                        </tr>
                        <tr>
                            <td>&nbsp;</td>
                        </tr>
                        <tr>
                            <td>
                                <table class="groupTable" align="center" width="80%">
                                    ${ tracks }
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

var limitedFieldManagerList = [];
var limitedFieldList = ${ limitedFieldList };
var mandatoryFieldList = ${ mandatoryFieldList };
mandatoryFieldList.push("abstractTitle"); // append the title id which is in this template
var pmMandatoryFields = new IndicoUtil.parameterManager();

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

function addPMToMandatoryFields() {
    for (var i=0; i<mandatoryFieldList.length; i++) {
        pmMandatoryFields.add($E(mandatoryFieldList[i]), null, false);
    }
}

function checkFields() {
    var condLimited = checkLimitedFields();
    var condMandatory = pmMandatoryFields.check();
    if (condLimited && condMandatory) {
        $E('formError').dom.style.display = "none";
        return true;
    } else {
        $E('formError').dom.style.display = "";
        return false;
    }
}

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
