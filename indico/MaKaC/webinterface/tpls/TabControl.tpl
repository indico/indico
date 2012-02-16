<div class="static-tabs" style="display:table; width:100%;" data-active="${activeTab}">
    <ul>
        % for i, (label, link, active, className) in enumerate(tabs):
            <li><a href="${('#static-tabs-%s-content' % tabControlId) if active else link}" ${'class='+className if className else ''} data-href="${link}">${label}</a></li>
        % endfor
    </ul>

    <div id="static-tabs-${tabControlId}-content">
        ${ body }
    </div>
</div>