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
    else:  # Conference
        event = target_.as_event
        name = event.title
        if isModif:
            url = url_for('event_management.settings', target_)
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
            <a href="${ url }" itemscope itemtype="http://data-vocabulary.org/Breadcrumb" itemprop="url">
                <span itemprop="title">${ truncateTitle(name, 40) | remove_tags }</span>
            </a>
        % endfor
    </span>
</div>
