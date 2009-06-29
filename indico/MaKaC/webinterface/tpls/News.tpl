<div class="container">
    <div class="groupTitle"><%= _("Latest News") %></div>

<div>
<% for newtype,newslist in news: %>
    <% if newslist: %>
        <div class="newsGroup">    
        <h2 class="newsTypeTitle"><%= newtype %></h2>
        <% for newitem in newslist: %>
            <div class="newsDisplayItem">
                <div class="newsDisplayItemDate"><%= formatDateTime(newitem.getCreationDate())%></div>
                <div style="display: inline;">
                    <div class="newsDisplayItemTitle"><%= newitem.getTitle() %></div>
                    <div class="newsDisplayItemContent"><%= newitem.getContent() %></div>
                </div>
            </div>
        <% end %>
    <% end %>
    </div>
<% end %>
</div>
</div>