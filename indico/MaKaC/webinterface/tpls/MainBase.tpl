% if not isFrontPage and navigation:
    ${ navigation }
% else:
    <div class="mainNoBreadcrumb">
    </div>
% endif

<div class="clearfix">
    % if isRoomBooking:
        % if sideMenu:
            <div class="emptyVerticalGap"></div>
        % endif
                % if sideMenu:
                <div>
                    ${ sideMenu }
                </div>
                % endif
                <div class="body clearfix${" bodyWithSideMenu" if sideMenu else ""}${" bodyWithSideBar" if isFrontPage else ""}" style="margin-left:0px;">
                        ${ body }
                </div>
           </div>
</div>

    % else:

       % if sideMenu:

           <div class="emptyVerticalGap"></div>
           ${ sideMenu }

       % endif

        % if isFrontPage:
            <div class="frontPageSideBarContainer">
                <div class="sideBar">
                  <div class="smallSideBox" style="margin-bottom: 20px;">
                    <h1>${ _("News") }</h1>
                        <%include file="WelcomeHeader.tpl" args="tz = timezone"/>
                  </div>
                  <div class="smallSideBox">
                    <h1>${ _("Upcoming events") }</h1>
                        ${ upcomingEvents }
                  </div>
                </div>
            </div>
        % endif

        <div class="body clearfix${" bodyWithSideMenu" if sideMenu else ""}${" bodyWithSideBar" if isFrontPage else ""}">
            ${ body }
        </div>
    % endif
</div>
