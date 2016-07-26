<%page args="news=None"/>

<ul id="news-list" class="main-page-list">
    % for item in news:
        <li>
            <a class="title" href="${ url_for('news.display', item.locator.anchor_only) }">${ item.title }</a>
            <span class="timing">${ _('Posted on') }&nbsp;${ formatDate(item.created_dt) }</span>
        </li>
    % endfor
</ul>
