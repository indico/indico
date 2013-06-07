<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <table width='100%'>
        <tr>
            <td>
                <table>
                    ${ items }
                </table>
            </td>
        </tr>
    </table>
</%block>
