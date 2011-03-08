% if material: 
    <div>
        ${ material }
    </div>
% endif

<ul class="list">
% for item in items: 
    <%include file="CategoryListItem.tpl" args="lItem=item, categoryDisplayURLGen=categoryDisplayURLGen"/>
% endfor
</ul>
