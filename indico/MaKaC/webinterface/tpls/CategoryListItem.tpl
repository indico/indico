<%page args="lItem=None, categoryDisplayURLGen=None"/>
<li>
      <span>
          <a href="${ categoryDisplayURLGen(lItem) }">${ escape(lItem.getName().strip()) or _("[no title]") }</a>

        <em>(${ lItem.getNumConferences() })</em>

        % if lItem.hasAnyProtection():
              <span class="protected">
                % if lItem.getDomainList() != []:
                    ${ "%s domain only"%(", ".join(map(lambda x: x.getName(), lItem.getDomainList()))) }
                % else:
                    ${ _("(protected)")}
                % endif
            </span>
        % endif
      </span>

</li>
