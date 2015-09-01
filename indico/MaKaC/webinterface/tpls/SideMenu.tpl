<%
    import re
    somethingVisible = False
%>

<div class="sideBar sideMenu ${"managementSideMenu" if sideMenuType != "basic" else ""}">
    % if sideMenuType != "basic":
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
                                <% liClass = "sideMenu_disabled" %>
                            % endif
                            % if menu.event and item.event_feature:
                                <% liClass = '{} js-event-feature-{}'.format(liClass, item.event_feature) %>
                                % if not menu.event.has_feature(item.event_feature):
                                    <% liClass += ' weak-hidden' %>
                                % endif
                            % endif

                            <li id="sideMenu_${ re.sub(r'[^a-zA-Z]', '', item.getTitle())}" class="${ liClass } ${ 'js-event-feature-{}'.format(item.event_feature) if menu.event and item.event_feature else '' }">
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
