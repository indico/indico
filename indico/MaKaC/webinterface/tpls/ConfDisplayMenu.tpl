% if menuStatus == "open" and menu:
  <!--Left menu-->
  <div class="conf_leftMenu">
    <ul id="outer" class="clearfix">
      % for link in menu.getEnabledLinkList():
        % if link.isVisible():

          % if link.getType() == "spacer":
            <%
              index = link.getParent().getLinkList().index(link)-1
              type = link.getParent().getLinkList()[index].getType()
            %>
            % if type in ["system", "extern"] and index != -1:
                 <li class="spacer"></li>
            % endif
          % else:
            <li id="menuLink_${link.getName()}"
              % if menu.isCurrentItem(link):
                class="menuConfTitle selected"
              % else:
                class="menuConfTitle"
              % endif
            >
              <a href="${link.getURL()}"
                 % if link.getType() == "extern":
                   target="${link.getDisplayTarget()}"
                 % endif
              >${link.getCaption()}</a>

            <ul class="inner">
            % for sublink in link.getEnabledLinkList():
              <li id="menuLink_${sublink.getName()}"
                   % if menu.isCurrentItem(sublink):
                     class="menuConfMiddleCell selected"
                   % else:
                     class="menuConfMiddleCell"
                   % endif
              >
                <a href="${sublink.getURL()}"
                   % if sublink.getType() == 'external':
                     target="${sublink.getDisplayTarget()}"
                   % endif
               >${_(sublink.getCaption())}</a>
              </li>
            % endfor
            </ul>
          </li>
          % endif
        % endif
      % endfor
    </ul>
    % if not support_info.isEmpty():
    <ul class="support_box">
      <h3>${support_info.getCaption()}</h3>
      % if support_info.hasEmail():
        % for email in support_info.getEmail().split(','):
          <li>
            <span class="icon icon-mail" aria-hidden="true"></span>
            <a href="mailto:${email}?subject=${event.getTitle() | h}"> ${email}</a>
          </li>
        % endfor
      % endif

      % if support_info.hasTelephone():
        <li>
          <span class="icon icon-phone" aria-hidden="true"></span>
          <a href="tel:${support_info.getTelephone().replace(' ', '')}"> ${support_info.getTelephone()}</a>
        </li>
      % endif
    </ul>
    % endif
  </div>
% endif
