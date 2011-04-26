<%include file="Announcement.tpl"/>

<div class="pageHeader pageHeaderMainPage clearfix">
        <%include file="SessionBar.tpl" args="dark=False"/>

        % if searchBox != '':
            ${ searchBox }
        % endif

        <!--
            set fixed height on anchor to assure that the height is
            corrected if the image cannot be retrieved (i.e. https problems) -->
        <a style="min-height: 66px;" href="${ urlHandlers.UHWelcome.getURL() }">
            <img class="headerLogo" src="${ imgLogo }" />
        </a>

        % if isFrontPage:
            <div class="headerAboutIndico">
                ${_("The Indico tool allows you to manage complex conferences, workshops and meetings.")}
            </div>
        % endif

    <div class="globalMenu">
        <ul>
            <li onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="${ urlHandlers.UHWelcome.getURL() }">${ _("Home") }</a></li>
            <li id="createEventMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><span class="dropDownMenu">Create event</span></li>

            % if roomBooking:
                <li onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="${ urlHandlers.UHRoomBookingWelcome.getURL() }">Room booking</a></li>
            % endif

            % if len(adminItemList) == 1:
                <li onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="${ adminItemList[0]['url'] }">text</a></li>
            % elif len(adminItemList) > 1:
                <li id="administrationMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><span class="dropDownMenu">Administration</span></li>
            % endif

            % if currentUser:
                <li onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="${ urlHandlers.UHUserDetails.getURL(currentUser) }">My profile</a></li>
            % endif

            <li id="helpMenu"  onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><span class="dropDownMenu">Help</span></li>
            <li style="display: none;" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="${ urlHandlers.UHContact.getURL() }">Contact</a></li>
            <li style="display: none;" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="${ urlHandlers.UHCategoryMap.getURL(categId=0) }">Site Map</a></li>
            <li style="display: none;" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="${ urlHandlers.UHAbout.getURL() }">About Indico</a></li>

            <li onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''" style="display: none;"><a href="urlHandlers.UHGetUserEventPage.getURL()">My Indico</a></li>
        </ul>
    </div>
</div>
