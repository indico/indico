<%
from MaKaC.webinterface.urlHandlers import UHHelper
from MaKaC.conference import Conference, Track
from MaKaC.review import Abstract
from indico.modules.categories.models.categories import Category

l = []

target_ = target
while target_ != None:
    if isinstance(target_, Category):
        for category in target_.chain_query[::-1]:
            if isModif:
                url = url_for('categories.manage_content', category)
            else:
                url = category.url
            l.append((category.title, url))
        break
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

    if isinstance(target_, Conference):
        target_ = target_.as_event.category
    elif not isinstance(target_, Abstract):
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

<div class="main-breadcrumb" ${'style="background-color: '+ bgColor +';" ' if bgColor else ""}>
    <span class="path">
        % for i in range (0, len(l)):
            % if i > 0:
                <span class="sep">»</span>
            % endif
            <% name, url = l[i] %>
            <a href="${ url }" itemscope itemtype="http://data-vocabulary.org/Breadcrumb" itemprop="url">
                <span itemprop="title">${ truncateTitle(name, 40) | remove_tags }</span>
            </a>
        % endfor
    </span>
</div>
