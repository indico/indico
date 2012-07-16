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
                        <a href='${track['url']}'>${track['title']}</a>
                    </div>
                    <div class="contributionListContribDescription">
                        ${track['description']}
                    </div>
                    % if track['subTracks']:
                    <div class="contributionListContribSpeakers">
                        ${_('Sub-Tracks')}:
                        % for subtrack in track['subTracks']:
                            ${subtrack},
                        % endfor
                    </div>
                    % endif
                </div>
            % endfor
        </td>
    </tr>
</table>
