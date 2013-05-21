% if shortUrls:
<tr>
    <td class="leftCol">Short URLS</td>
    <td>
    % for id, url in shortUrls:
    <div class="CRDisplayInfoLine">
        <span>${id}:</span><span style="margin-left: 20px;"><a href='${url}'>${url}</span>
    </div>
    % endfor
    </td>
</tr>
% endif
