<ul class="category-list">
% for item in items:
    <%include file="CategoryListItem.tpl" args="lItem=item, categoryDisplayURLGen=categoryDisplayURLGen"/>
% endfor
</ul>
