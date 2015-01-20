
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
<table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td colspan="2">
            ${ contents }
            <br>
            <br>
            <table cellpadding="0" cellspacing="0" width="100%">
                 <tr>
                        <td colspan="2" align="right"> ${ _("Updated") } ${ updated }
                        </td>
                  </tr>
            </table>
        </td>
    </tr>
</table>
</div>
