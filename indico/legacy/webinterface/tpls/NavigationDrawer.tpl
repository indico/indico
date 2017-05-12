<%
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
    else:  # Event
        event = target_
        name = event.title
        if isModif:
            url = url_for('event_management.settings', event)
        else:
            url = event.url
        target_ = event.category

    l.append((name, url))

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
            <a href="${ url }" itemscope itemtype="http://data-vocabulary.org/Breadcrumb" itemprop="url" class="item">
                <span itemprop="title">${ escape(truncateTitle(name, 40)) }</span>
            </a>
        % endfor
    </span>
</div>
