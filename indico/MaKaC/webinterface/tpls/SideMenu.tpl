<% somethingVisible = False %>

<div class="sideBar sideMenu ${"managementSideMenu" if sideMenuType != "basic" else ""}">
% if sideMenuType == "basic":
<div class="leftCorner"></div>
<div class="rightCorner"></div>
%else:
<div class="corner"></div>
% endif

<div class="content">
<ul>

% for i, section in enumerate(menu.getSections()):
    % if section.isVisible():
        <% somethingVisible = True %>

        % if section.getTitle():
            <% menuHeaderClass = "" %>
            % if section.isActive():
                <% menuHeaderClass = "active" %>
            % endif
            <li class="separator">${ section.getTitle() }</li>
        % elif i >= 1:
            <li class="separatorNoText"></li>
        % endif

        % for item in section.getItems():
            % if item.isVisible():
                <% liClass = "" %>
                % if item.isEnabled():
                    % if item.isActive():
                        <% liClass = "active" %>
                    % endif
                % else:
                    <% liClass = "sideMenu_disabled " + item.getErrorMessage() %>
                % endif

                <li id="sideMenu_${ item.getTitle().replace(' ','')} " class="${ liClass }">
                    % if item.isEnabled():
                        <a href="${ item.getURL() }">
                            ${ item.getTitle() }
                        </a>
                    % else:
                        ${ item.getTitle() }
                    % endif
                </li>
            % endif
        % endfor

    % endif
% endfor

% if not somethingVisible:
&nbsp;
% endif
</ul>
</div>
</div>
