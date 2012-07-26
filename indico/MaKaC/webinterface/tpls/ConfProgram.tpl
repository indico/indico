<div class="groupTitle">
    ${ _("Scientific Programme")}
</div>
<table width="100%" cellspacing="0">
    <tr>
        <td>
            <font color="black">${ description }</font>
        </td>
    </tr>
    <tr>
        <td>&nbsp;</td>
    </tr>
    <tr>
        <td>
            % for track in program:
                <div class='contributionListContribItem'>
                    <div class="contributionListContribHeader">
                    % if 'url' in track:
                        <a href='${track['url']}'>${track['title']}</a>
                    % else:
                        ${track['title']}
                    % endif
                    </div>
                    <div class="contributionListContribDescription">
                        ${track['description']}
                    </div>
                </div>
            % endfor
        </td>
    </tr>
</table>
