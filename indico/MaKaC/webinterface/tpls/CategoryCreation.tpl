
<form id="categCreationForm" action="${ postURL }" method="POST">
    ${ locator }
    <table class="groupTable">
        <tr>
            <td colspan="2"><div class="groupTitle">${ _("Creation of a new sub-category")}</div></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Name")}</span></td>
            <td class="blacktext"><input type="text" name="name"></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Description")}</span></td>
            <td class="blacktext">
                <textarea name="description" cols="43" rows="6"></textarea>
            </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Default lectures style")}</span></td>
            <td class="blacktext"><select name="defaultSimpleEventStyle">${ simple_eventStyleOptions }</select></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Default meetings style")}</span></td>
            <td class="blacktext"><select name="defaultMeetingStyle">${ meetingStyleOptions }</select></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Default Timezone")}</span></td>
            <td class="blacktext"><select name="defaultTimezone">${ timezoneOptions }</select></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Protection")}</span></td>
            <td class="blacktext">
                <div>
                    % if categProtection == 'public' :
                        <% color = "#128F33" %>
                    % else :
                        <% color = "#B02B2C" %>
                    % endif
                    <span id="inheritRadioButtonWrapper" class="categProtectionRadioEntry">
                        <input type="radio" id="inheritRadioButton" class="eventProtectionRadioButton" name="categProtection" value='inherit' onclick="hideUserList();" checked/><label for="inheritRadioButton"><span id="inheritRadioEntryKey" style="color:${ color };">${ _("Same as for parent category '") }<span id="radioCategTitle">${ categTitle }</span>'</span> : <span id="radioCategProtection" style="font-weight: bold;">${ categProtection }</span> ${ _("for the moment, but it may change") } </label>
                    </span>
                    <span id="privateRadioButtonWrapper" class='categProtectionRadioEntry'>
                        <input type="radio" id="privateRadioButton" class="eventProtectionRadioButton" name="categProtection" value='private' onclick="showUserList();"/><label for="privateRadioButton"><span style="color: #B02B2C">${ _("Restricted") }</span>${ _(" : Can only be viewed by you and users/groups chosen by you from the list of users") }</label>
                    </span>
                    <span id="allowedUserListInfo" class="allowedUserListInfo" style="display: none;">
                        <em>${ _("Please fill in the list below with the users/groups that will be granted access to this category. You can always do so later, once the category is created, through the category protection settings.") }</em>
                    </span>
                    <div id="userListWrapper">
                    </div>
                    % if categProtection != 'public' :
                    <span id="publicRadioButtonWrapper" class='categProtectionRadioEntry'>
                        <input type="radio" id="publicRadioButton" class="eventProtectionRadioButton" name="categProtection" value='public' onclick="hideUserList();"/><label for="publicRadioButton"><span style="color: #128F33">${ _("Public") }</span>${ _(" : Can be viewed by everyone") }</label>
                    </span>
                    % endif
                </div>
                <input type="hidden" value="" id="allowedUsers" name="allowedUsers"/>
            </td>
        </tr>
        % if numConferences:
            <tr>
                <td colspan="2" class="categoryWarning">
                    <p class="warningText">${_('<strong>Warning:</strong> The parent category contains %d events which will be moved to the new sub-category.') % numConferences}</p>
                </td>
            </tr>
        % endif
        <tr>
            <td>&nbsp;</td>
            <td>
                <input type="submit" class="btn" name="OK" value="${ _("Create Sub-Category")}">
                <input type="submit" class="btn" name="cancel" value="${ _("Cancel")}">
            </td>
        </tr>
    </table>
</form>

<script type="text/javascript">

    // ---- List of users allowed to view the event

    var allowedUsersList = new UserListField(
            'allowedUserListDiv', 'allowedUserList',
            null, true, null,
            true, true, null, null,
            false, false, false, true,
            userListNothing, userListNothing, userListNothing);

    // ---- When the private radio button is selected, display the list of users

    var hideUserList = function() {
        $E('userListWrapper').dom.style.padding = "";
        $E('userListWrapper').set('');
        $E('allowedUserListInfo').dom.style.display = "none";
    }

    var showUserList = function() {
        $E('userListWrapper').dom.style.padding = "6px 26px";
        $E('userListWrapper').set(allowedUsersList.draw());
        $E('allowedUserListInfo').dom.style.display = "";
    }

    function injectValuesInForm(form, action) {
        form.observeEvent('submit', function() {
            if (action) {
               return action();
            }
         });
       };

    // ---- On Load
    IndicoUI.executeOnLoad(function() {
        injectValuesInForm($E('categCreationForm'),function() {
            $E('allowedUsers').set(Json.write(allowedUsersList.getUsers()));
        });
    });

</script>
