<%page args="lItem=None, categoryDisplayURLGen=None"/>
<li>
      <span>
          <a href="${ categoryDisplayURLGen(lItem) }">${ escape(lItem.getName().strip()) or _("[no title]") }</a>

       <% nconf = lItem.getNumConferences() %>
       <span class="num_events">
         % if nconf == 0:
           ${_("empty")}
         % else:
           ${N_('%s event',
                '%s events', nconf) % format_number(nconf)}
         % endif
       </span>
        % if lItem.hasAnyProtection():
              <span class="protected">
                % if lItem.getDomainList() != []:
                    ${ "(%s domain only)"%(", ".join(map(lambda x: x.getName(), lItem.getDomainList()))) }
                % else:
                    ${ _("(protected)")}
                % endif
            </span>
        % endif
      </span>

</li>
