<%page args="tz=None"/>
<%
from indico.modules import ModuleHolder
from MaKaC.common.timezoneUtils import DisplayTZ
newsModule = ModuleHolder().getById("news")
newsList = newsModule.getNewsItemsList()
%>

<ul>
    % for newItem in newsList[:2]:
        <li>
            <a href="${ urlHandlers.UHIndicoNews.getURL()}">
                ${ newItem.getTitle() }
            </a>
            <em>${ _('Posted on') }&nbsp;${ formatDate(newItem.getAdjustedCreationDate(tz)) }</em>
        </li>
    % endfor
</ul>
<div style="margin-top:10px; text-align: right;">
    <a href="${ urlHandlers.UHIndicoNews.getURL()}" class="subLink">${ _("View news history") }</a>
</div>
