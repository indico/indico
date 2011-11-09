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
        <table border="0" cellSpacing="0" cellPadding="0">
            <tr>
                % if sideMenu:
                <td style="vertical-align: top;">
                    ${ sideMenu }
                </td>
                % endif
                <td style="vertical-align: top; width: 100%;">
                    <div class="body clearfix${" bodyWithSideMenu" if sideMenu else ""}${" bodyWithSideBar" if isFrontPage else ""}" style="margin-left:0px;">
                        ${ body }
                    </div>
                </td>
            </tr>
        </table>

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
                % if upcomingEvents:
                <div class="smallSideBox" style="margin-bottom: 20px;">
                    <h1>${ _("Upcoming events") }</h1>
                        ${ upcomingEvents }
                </div>
                % endif
              </div>
            </div>
        % endif

        <div class="body clearfix${" bodyWithSideMenu" if sideMenu else ""}${" bodyWithSideBar" if isFrontPage else ""}">
            ${ body }
        </div>
    % endif
</div>
