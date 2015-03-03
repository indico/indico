<div class="container">
    <h2 class="page-title">${ _("Latest News") }</h2>

    <div>
    % for newsItem in news:
        <div class="news-item">
            <div class="right news-item-info">
                <span class="date-time">${ formatDate(newsItem.getAdjustedCreationDate(tz))}</span> -
                <span class="news-type">${ newsItem.getHumanReadableType() }</span>
            </div>
            <h2>${ newsItem.getTitle() }
                % if newsItem.isNew():
                    <i class="icon-new new-label"></i>
                % endif
            </h2>
            <div class="content">${ newsItem.getContent() }</div>
        </div>
    % endfor
    </div>
</div>
