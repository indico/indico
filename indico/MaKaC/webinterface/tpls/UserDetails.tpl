<table class="groupTable">
    <tr>
        <td colspan="2" align="right">
            <em>
                 ${ _("""This page shows your personal data. You can modify it by clicking on the 'modify' button.<br>
                You can also find the different accounts you can use to login. You can add or remove accounts, <br>
                but you must have at least one account.""")}
            </em>
        </td>
    </tr>
    <tr>
        <td colspan="2">
            <div class="groupTitle">${ _("Details for") } <span id="titleHeader">${ title }</span>
                <span id="surNameHeader">${ surName.upper() },</span>
                <span id="firstNameHeader">${ name }</span>
            </div>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Title")}</span></td>
        <td class="blacktext" style="width:100%">
            <div id="inPlaceEditTitle"></div>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Family Name")}</span></td>
        <td class="blacktext">
            <div id="inPlaceEditSurName"></div>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("First Name")}</span></td>
        <td class="blacktext">
            <div id="inPlaceEditName"></div>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Affiliation")}</span></td>
        <td class="blacktext">
            <div id="inPlaceEditOrganisation"></div>
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Email")}</span></td>
        <td class="blacktext">
            <div id="inPlaceEditEmail"></div>
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Secondary emails")}</span></td>
        <td class="blacktext">
            <div id="inPlaceEditSecondaryEmails"></div>
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Address")}</span></td>
        <td class="blacktext" style="padding-left:5px;">
            <pre id="inPlaceEditAddress">${ address }</pre>
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Telephone")}</span></td>
        <td class="blacktext">
            <div id="inPlaceEditTelephone"></div>
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Fax")}</span></td>
        <td class="blacktext">
            <div id="inPlaceEditFax"></div>
        </td>
    </tr>
    <tr>
        <td colspan="2" ><div class="groupTitle">${ _("Your account(s)")}</div></td>
    </tr>
        <td nowrap class="dataCaptionTD">
            <span class="dataCaptionFormat">${ _("Account status")}</span>
        </td>
        <td bgcolor="white" nowrap valign="top" class="blacktext">
            ${ status }
            ${ activeButton }
        </td>
    </tr>
    <tr>
        <td>&nbsp;</td>
        <td class="blacktext">
            ${ identities }
        </td>
    </tr>
    <tr>
        <td colspan="2" >
            <div class="groupTitle">${ _("Special Rights")}</div>
        </td>
   </tr>
   <tr>
        <td nowrap class="dataCaptionTD">
            <span class="dataCaptionFormat">${ _("Category Manager")}</span>
        </td>
        <td class="blacktext">
            ${ categoryManager }
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD">
            <span class="dataCaptionFormat">${ _("Event Manager")}</span>
        </td>
        <td class="blacktext">
            ${ eventManager }
        </td>
    </tr>
</table>

<script>

var unlockedFields = ${jsonEncode(unlockedFields)};
var canSynchronize = !_.isEmpty(Indico.Settings.ExtAuthenticators);
var authenticatorName = canSynchronize && Indico.Settings.ExtAuthenticators[0][1];
var syncOffIcon = $('<img/>', {src: '${Config.getInstance().getSystemIconURL("syncOff")}'});
var syncOnIcon = $('<img/>', {src: '${Config.getInstance().getSystemIconURL("syncOn")}'});
var syncOnMsg = $T('This field is currently synchronized with the {0} database.').format(authenticatorName);
var syncOffMsg = $T('You changed this field manually. To synchronize it with the {0} database, click this icon.').format(authenticatorName);

var makeSyncInfo = function(on) {
    var icon = on ? syncOnIcon : syncOffIcon;
    var msg = on ? syncOnMsg : syncOffMsg;
    var syncInfo = $('<span/>').css('margin-left', '3px').append(icon.clone());
    syncInfo.mousemove(function(e) {
        IndicoUI.Widgets.Generic.tooltip(this, e, msg);
    });
    return syncInfo;
}

var unlockField = function(field) {
    var self = this;
    if(!canSynchronize) {
        return;
    }
    if(!_.contains(unlockedFields, field)) {
        unlockedFields.push(field);
    }
    var lockLink = $('<a href="#"/>').css('margin-left', '3px').append(makeSyncInfo(false)).click(function(e) {
        e.preventDefault();
        var killProgress = IndicoUI.Dialogs.Util.progress();
        indicoRequest('user.syncPersonalData', {
            userId: '${ userId }',
            dataType: field
        }, function(result, error) {
            killProgress();
            if(error) {
                IndicoUtil.errorReport(error);
                return;
            }
            lockField(field);
            if(!result.val) {
                alert($T('Synchronization has been re-enabled for this field. To update the data with the {0} database, you need to log out and then login again.').format(authenticatorName));
            }
            else {
               self.value = result.val;
               if(field == 'firstName' || field == 'surName') {
                   $E(field + 'Header').set(result.val);
               }
            }
            self.modeChooser.set('display');
            $(self.wcanvas.dom).find('a').after(makeSyncInfo(true));
        });
    });
    $(this.wcanvas.dom).find('a').after(lockLink);
};

var lockField = function(field) {
    if(!canSynchronize) {
        return;
    }
    unlockedFields = _.without(unlockedFields, field);
};

var showAsSynchronized = function(field) {
    if(!canSynchronize) {
        return;
    }
    $(this.wcanvas.dom).find('a').after(makeSyncInfo(true));
}

var requestFirstName = function() {
    $E('firstNameHeader').set(this.value);
    unlockField.call(this, 'firstName');
};

var requestSurName = function() {
    $E('surNameHeader').set(this.value.toUpperCase()+',');
    unlockField.call(this, 'surName');
};

var requestTitle = function() {
    $E('titleHeader').set(this.value);
};

var beforeEdit = function(field) {
    if(!canSynchronize) {
        return;
    }
    if(!_.contains(unlockedFields, field) && !confirm($T('This field is currently synchronized with the {0} database. If you change it, synchronization will be disabled.').format(authenticatorName))) {
        return false;
    }
}


$E('inPlaceEditTitle').set(new SelectEditWidget('user.setPersonalData',
        {'userId':'${ userId }', 'dataType':'title'}, ${ titleList }, '${ title }', requestTitle).draw());

var editSurName =  new InputEditWidget('user.setPersonalData',
        {'userId':'${ userId }', 'dataType':'surName'}, '${ surName }', false, requestSurName, null, null, null,
        curry(beforeEdit, 'surName'));
$E('inPlaceEditSurName').set(editSurName.draw());

var editFirstName = new InputEditWidget('user.setPersonalData',
        {'userId':'${ userId }', 'dataType':'name'}, '${ name }', false, requestFirstName, null, null, null,
        curry(beforeEdit, 'firstName'));
$E('inPlaceEditName').set(editFirstName.draw());

var editOrganisation = new InputEditWidget('user.setPersonalData',
        {'userId':'${ userId }', 'dataType':'organisation'}, '${ organisation }', false, curry(unlockField, 'affiliation'), null, null, null,
        curry(beforeEdit, 'affiliation'));
$E('inPlaceEditOrganisation').set(editOrganisation.draw());

$E('inPlaceEditEmail').set(new InputEditWidget('user.setPersonalData',
        {'userId':'${ userId }', 'dataType':'email'}, '${ onlyEmail }', false, null, Util.Validation.isEmailAddress,
        $T("Invalid e-mail address")).draw());

$E('inPlaceEditAddress').set(new TextAreaEditWidget('user.setPersonalData',
        {'userId':'${ userId }', 'dataType':'address'}, $E('inPlaceEditAddress').dom.innerHTML, true).draw());

var editTelephone = new InputEditWidget('user.setPersonalData',
        {'userId':'${ userId }', 'dataType':'telephone'}, '${ telephon }', true, curry(unlockField, 'phone'), null, null, null,
        curry(beforeEdit, 'phone'));
$E('inPlaceEditTelephone').set(editTelephone.draw());

var editFax = new InputEditWidget('user.setPersonalData',
        {'userId':'${ userId }', 'dataType':'fax'},'${ fax }', true, curry(unlockField, 'fax'), null, null, null,
        curry(beforeEdit, 'fax'));
$E('inPlaceEditFax').set(editFax.draw());

$E('inPlaceEditSecondaryEmails').set(new InputEditWidget('user.setPersonalData',
        {'userId':'${ userId }', 'dataType':'secondaryEmails'}, '${ secEmails }', true, null, Util.Validation.isEmailList,
        $T("List contains invalid e-mail address or invalid separator"),
        $T("You can specify more than one email address separated by commas, semicolons or whitespaces.")).draw());

$.each({
    surName: editSurName,
    firstName: editFirstName,
    affiliation: editOrganisation,
    phone: editTelephone,
    fax: editFax
}, function(field, editor) {
    if(_.contains(unlockedFields, field)) {
        unlockField.call(editor, field);
    }
    else {
        showAsSynchronized.call(editor, field);
    }
});
</script>
