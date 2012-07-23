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
            <td style="width:30px;">${contrib['id']}</td>
            <td style="width:250px;"><a href=${contrib['displayURL']}>${contrib['title']}</a></td>
            <td>${contrib['startDate']}</td>
            <td>${contrib['duration']}</td>
            <td>${contrib['type']}</td>
            <td style="width:150px;">${contrib['speakers']}</td>
        </tr>
    % endfor
    </tbody>
</table>