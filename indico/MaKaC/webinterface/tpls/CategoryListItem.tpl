<%page args = "lItem=None, categoryDisplayURLGen=None"/>
<% nconf = lItem.getNumConferences() %>
<% prot = getProtection(lItem) %>

<li>
    % if prot[0]:
        % if prot[0] == "domain":
            <span class="protection icon-shield" data-type="domain" data-domain="${prot[1] | n, j, h}"></span>
        % else:
            <span class="protection icon-shield" data-type="restricted"></span>
        % endif
    % endif

    <span class="number-events" style="${"margin-right: 2em;" if not prot[0] else ""}">
        % if nconf == 0:
            ${_("empty")}
        % else:
            ${N_('%s event', '%s events', nconf) % format_number(nconf)}
        % endif
    </span>

    <a href="${categoryDisplayURLGen(lItem)}" class="name">${lItem.getName().strip() or _("[no title]") | remove_tags, h}</a>
</li>
