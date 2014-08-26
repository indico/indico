<%inherit file="Administrative.tpl"/>

<%!
    allMaterial = False
    hideTime = False
    materialSession = True
    showOrder = False
    print_mode = True
%>

<%block name="header">
    <table class="eventHeader">
        <tr>
            <td>
                <div style="float:left;">
                    <img src="${Config.getInstance().getBaseURL()}/images/smallcern.png"/>
                </div>
                <br/>
                <div class="eventHeader">${ category }</div>
            </td>
        </tr>
    </table>
</%block>
<%block name="locationAndTime">
</%block>
