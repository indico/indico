<%
from MaKaC.webinterface.urlHandlers import UHHelper
from MaKaC.conference import Category
from MaKaC.conference import Track
from MaKaC.review import Abstract
from MaKaC.common import Configuration

l = []

target_ = target
while target_ != None:
    if type(target_) == Category:
        name = target_.getName()
    else:
        name = target_.getTitle()

    if isModif:
        url = UHHelper.getModifUH(type(target_)).getURL(target_)
    else:
        if actionType:
            catType = actionType
        else:
            catType = ''
        url = UHHelper.getDisplayUH(type(target_), catType).getURL(target_)

    l.append( (name, url) )

    if type(target_) != Abstract:
        target_ = target_.getOwner()
    else:
        if track:
            if isModif:
                url = UHHelper.getModifUH(Track).getURL(track)
            else:
                url = UHHelper.getDisplayUH(Track).getURL(track)
            l.append( (track.getTitle(), url) )
        target_ = target_.getOwner().getOwner()


l.reverse()

arrowImage = systemIcon( "breadcrumb_arrow.png" )

%>

<div class="mainBreadcrumb" ${'style="background-color: '+ bgColor +';" ' if bgColor else ""}>
<span class="path">
    % for i in range (0, len(l)):
        % if i > 0:
            <img src="${ arrowImage }" />
        % endif
        <% name, url = l[i] %>
        <a href="${ url }" itemscope itemtype="http://data-vocabulary.org/Breadcrumb" itemprop="url">
            <span itemprop="title">${ truncateTitle(name, 40) | remove_tags }</span>
        </a>
    % endfor
</span>
</div>
