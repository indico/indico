% if not isFrontPage and navigation:
    ${ navigation }
% else:
    <div class="mainNoBreadcrumb">
    </div>
% endif

<div class="clearfix">
    % if isRoomBooking:
        % if sideMenu:
            <div class="layout-side-menu">
                <div class="menu-column">
                    ${ sideMenu }
                </div>
                <div class="content-column">
                    ${ render_template('flashed_messages.html') }
                    ${ body }
                </div>
            </div>
        % else:
            ${ render_template('flashed_messages.html') }
            ${ body }
        % endif
    % else:
       % if sideMenu:
           ${ sideMenu }
       % endif

        <div class="body clearfix${" bodyWithSideMenu" if sideMenu else ""}">
            ${ body }
        </div>
    % endif
</div>
