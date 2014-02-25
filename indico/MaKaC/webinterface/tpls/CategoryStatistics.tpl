<div class="category-container">
    <div class="category-header">
        <h1 class="category-title sidebar-padding">
            ${ name | remove_tags }&nbsp;
            <span style="font-style: italic; font-size: 0.8em;">(${ _("statistics") })</span>
        </h1>
        <div class="right">
            <li><a href="${ categDisplayURL }">${ _("Go back to category page") }</a></li>
        </div>
    </div>

    <div class="category-content-wrapper category-statistics">
        ${ contents }
        <br>
        <br>
        <div class="right"> ${ _("Updated") } ${ updated }</div>
    </div>
</div>
