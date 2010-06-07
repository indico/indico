<%from MaKaC.webinterface import urlHandlers %>
<div class="mainBreadcrumb" <% if bgColor: %>style="background-color: <%= bgColor %>;" <% end %>>
<span class="path">
    <a href="<%= urlHandlers.UHWelcome.getURL() %>">
        <%= _("Home") %>
    </a>
   <img src="<%= systemIcon( "breadcrumb_arrow.png" ) %>" />
</span>

    <a href="<% if urlHandler: %><%= urlHandler(**pars) %><% end %><% else: %>#<%end%>">
        <%= title %>
    </a>
</span>
</div>