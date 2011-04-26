<div class="container">
    <div class="groupTitle">${ _("Latest News") }</div>

<div>
% for newsItem in news:
    <div class="newsDisplayItem">
        <div class="newsDisplayItemDateType">
            ${ formatDate(newsItem.getAdjustedCreationDate(tz))}
            -
            ${ newsItem.getHumanReadableType() }
        </div>
        <div style="display: inline;">
            <div class="newsDisplayItemTitle">${ newsItem.getTitle() }</div>
            % if newsItem.isNew():
            <img src="${ systemIcon('new') }" style="padding-left: 10px" alt="new" />
            % endif
            <div class="newsDisplayItemContent">${ newsItem.getContent() }</div>
        </div>
    </div>
% endfor
</div>
</div>
