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
    <li><a href="${ urlHandlers.UHIndicoNews.getURL()}" class="subLink">${ _("View news history") }</a></li>
</ul>
