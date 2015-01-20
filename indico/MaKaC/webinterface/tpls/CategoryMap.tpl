<div class="container categoryMap">
    <div class="categoryHeader">
        <ul>
            <li><a href="${ categDisplayURL }">${ _("Go back to category page") }</a></li>
        </ul>
        <h1 class="categoryTitle">
            ${ categName | remove_tags }&nbsp;
            <span style="font-style: italic; font-size: 0.8em;">(${ _("category map") })</span>
        </h1>
    </div>

<table width="100%">
    <tr>
        <td>
            <table width="100%" cellspacing="0" cellpadding="0" align="left">
                <tr>
                    <td bgcolor="gray">
                            <table width="100%" bgcolor="white"
                                    cellpadding="0" cellspacing="1">
                                <tr>
                                    <td>
                                       ${ map }
                                    </td>
                                </tr>
                            </table>
                        </form>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</div>
