<div class="main-breadcrumb">
    <span class="path">
        <a href="${ url_for_index() }" class="item">${ _("Home") }</a>

        % for item in items:
            <span class="sep">»</span>
            <span class="item">${ item }</span>
        % endfor
    </span>
</span>
</div>
