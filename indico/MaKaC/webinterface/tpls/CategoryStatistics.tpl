<div class="container">
    <div class="categoryHeader">
        <ul>
            <li><a href="${ categDisplayURL }">${ _("Go back to category page") }</a></li>
        </ul>
        <h1 class="categoryTitle">
            ${ name | remove_tags }&nbsp;
            <span style="font-style: italic; font-size: 0.8em;">(${ _("statistics") })</span>
        </h1>
    </div>

<br>
${ contents }
<br>
<br>
<div align="right"> ${ _("Updated") } ${ updated }</div>
</div>
