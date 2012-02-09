% if items:
    <table cellpadding="0" cellspacing="1">
        <tr>
        % for item in items:
            <td align="right" nowrap>
                <a href="${item.getActionURL()}" ${'id=' + item.getElementId() if item.getElementId() else ''} ${'class='+item.getClassName() if item.getClassName() else ''} ${'data-id='+item.getId() if item.getId() else ''}>
                    <img src="${str(item.getIcon())}" alt="${item.getCaption()}">
                </a>
            </td>
        % endfor
        </tr>
    </table>
% endif