<%
from MaKaC.webinterface.urlHandlers import UHHelper
from MaKaC.conference import Conference
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
    else:
        target_ = target_.getOwner()

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
                <span itemprop="title">${ escape(truncateTitle(name, 40)) }</span>
            </a>
        % endfor
    </span>
</div>
