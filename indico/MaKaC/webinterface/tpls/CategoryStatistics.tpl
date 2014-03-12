<div class="category-container">
    <div class="category-header">
        <div class="category-statistics center">
            <span class="right">
                <a class="i-button icon-arrow-left2" href="${ categDisplayURL }" style="margin-top:0.4em;">${ _('Category page')}</a>
            </span>
            <div class="category-title" style="margin-left:0px; text-align:left;">
                ${ name | remove_tags }&nbsp;
                <span style="font-style: italic; font-size: 0.8em;">(${ _("statistics") })</span>
            </div>
        </div>
    </div>

    <div class="category-content-wrapper category-statistics center">
        ${ plots }
        <div style="text-align:left;">
            ${ contents }
        </div>
        <br>
        <br>
        <div class="footer right"> ${ _("Updated") } ${ updated }</div>
    </div>
</div>
