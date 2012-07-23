<table width="100%">
    <thead>
        <tr class="trBottomSpacer">
            % for link in links:
                % if link['url'] and link['active']:
                <td><img src=${downArrow} /> ${link['label']}</td>
                % elif link['url']:
                <td><a href="${link['url']}">${link['label']}</a></td>
                % else:
                <td>${link['label']}</td>
                % endif
            % endfor
        </tr>
    </thead>
    <tbody>
    % for contrib in contribs:
        <tr>
            <td>${contrib['id']}</td>
            <td><a href=${contrib['displayURL']}>${contrib['title']}</a></td>
            <td>${contrib['speakers']}</td>
            <td>${contrib['boardNumber']}</td>
        </tr>
    % endfor
    </tbody>
</table>