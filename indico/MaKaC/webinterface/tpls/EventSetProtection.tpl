<%page args="eventType=None"/>

    <div class="groupTitle">${ _("Step 3: Set the access protection of the ") }${ eventType }</div>
    <div class="accessProtection">
        <span id="protectionRadioInfo" class="protectionRadioInfo"><em>${ _("Please choose a Category first in order to be able to set the protection.") }</em></span>
        <span id="inheritRadioButtonWrapper" class="eventProtectionRadioEntry">
            <input type="radio" id="inheritRadioButton" class="eventProtectionRadioButton" name="eventProtection" value='inherit' onclick="hideUserList();"/><label for="inheritRadioButton"><span id="inheritRadioEntryKey">${ _("Same as for Category '") }<span id="radioCategTitle">${ categ["title"] }</span>'</span> : <span id="radioCategProtection" style="font-weight: bold;">${ protection }</span> ${ _("for the moment, but it may change") }</label>
        </span>
        <span id="privateRadioButtonWrapper" class='eventProtectionRadioEntry'>
            <input type="radio" id="privateRadioButton" class="eventProtectionRadioButton" name="eventProtection" value='private' onclick="showUserList();"/><label for="privateRadioButton"><span style="color: #B02B2C">${ _("Restricted") }</span>${ _(" : Can only be viewed by you and users/groups chosen by you from the list of users") }</label>
        </span>
        <span id="userListInfo" class="userListInfo" style="display: none;">
            <em>${ _("Please fill in the list below with the users/groups that will be granted access to this event. You can always do so later, once the event is created, through the event protection settings.") }</em>
        </span>
        <div id="userListWrapper" class="userListWrapper">
        </div>
        <span id="publicRadioButtonWrapper" class='eventProtectionRadioEntry'>
            <input type="radio" id="publicRadioButton" class="eventProtectionRadioButton" name="eventProtection" value='public' onclick="hideUserList();"/><label for="publicRadioButton"><span style="color: #128F33">${ _("Public") }</span>${ _(" : Can be viewed by everyone") }</label>
        </span>
    </div>
    <input type="hidden" value="" id="allowedUsers" name="allowedUsers"/>

    <script type="text/javascript">

        function updateProtectionChooser(categTitle, categProtection)
        {
            $E("protectionRadioInfo").dom.style.display = "none";
            $E("inheritRadioButton").dom.disabled = false ;
            $E("inheritRadioButton").dom.checked = true ;
            $E("inheritRadioButtonWrapper").dom.style.display = "";
            $E("privateRadioButton").dom.disabled = false ;
            $E("publicRadioButton").dom.disabled = false ;

            // If the private option was selected before changing the
            // category
            this.hideUserList();

            if (categProtection != 'public') {
                $E("publicRadioButtonWrapper").dom.style.display = "";
                $E("inheritRadioEntryKey").dom.style.color = "#B02B2C";
            } else {
                $E("publicRadioButtonWrapper").dom.style.display = "none";
                $E("inheritRadioEntryKey").dom.style.color = "#128F33";
            }

            $E("radioCategTitle").set(categTitle);
            $E("radioCategProtection").set(categProtection);

        }

        function injectFromProtectionChooser()
        {
            if(!($E("privateRadioButton").dom.checked)) {
                allowedUsersList.clear();
            }

            $E('allowedUsers').set(Json.write(allowedUsersList.getUsers()));
        }

        function protectionChooserExecOnLoad(categId, categProtection) {

            if (categId != ""){
                $E("protectionRadioInfo").dom.style.display = "none";
                $E("inheritRadioButton").dom.checked = true ;
                if (categProtection == "public") {
                    $E("inheritRadioEntryKey").dom.style.color = "#128F33";
                    $E("publicRadioButtonWrapper").dom.style.display = "none";
                }
                else {
                    $E("inheritRadioEntryKey").dom.style.color = "#B02B2C";
                }
            }
            else {
                $E("inheritRadioButtonWrapper").dom.style.display = "none";
                $E("inheritRadioButton").dom.disabled = true ;
                $E("publicRadioButton").dom.checked = true ;
                $E("privateRadioButton").dom.disabled = true ;
                $E("publicRadioButton").dom.disabled = true ;
            }
        }

        // ---- List of users allowed to view the event

        var allowedUsersList = new UserListField(
                'userListDiv', 'userList',
                null, true, null,
                true, true, null, null,
                false, false, false, true,
                userListNothing, userListNothing, userListNothing);

        // ---- When the private radio button is selected, display the list of users

        var hideUserList = function() {
            $E('userListWrapper').set('');
            $E('userListInfo').dom.style.display = "none";
        }

        var showUserList = function() {
            $E('userListWrapper').set(allowedUsersList.draw());
            $E('userListInfo').dom.style.display = "";
        }

    </script>
