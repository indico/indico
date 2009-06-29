<% somethingVisible = False %>

<div class="sideBar sideMenu <% if sideMenuType != "basic": %>managementSideMenu<%end%>">
<% if sideMenuType == "basic": %>
<div class="leftCorner"></div>
<div class="rightCorner"></div>
<%end%>
<%else:%>
<div class="corner"></div>
<%end%>

<div class="content">
<ul>

<% for i, section in enumerate(menu.getSections()): %>
    <% if section.isVisible(): %>
        <% somethingVisible = True %>
        
        <% if section.getTitle(): %>
            <% menuHeaderClass = "" %>
            <% if section.isActive(): %>
                <% menuHeaderClass = "active" %>
            <% end %>
            <li class="separator"><%= section.getTitle() %></li>
        <% end %>
        <% elif i >= 1: %>
            <li class="separatorNoText"></li>
        <% end %>
      
        <% for item in section.getItems(): %>
            <% if not item.isVisible(): continue %><%end%>
            
            <% liClass = "" %>
            <% if item.isEnabled(): %>
                <% if item.isActive(): %>
                    <% liClass = "active" %>
                <% end %>
            <% end %>
            <% else: %>        
                <% liClass = "sideMenu_disabled " + item.getErrorMessage() %>
            <% end %>
            
            <li id="sideMenu_<%= item.getTitle().replace(' ','')%> " class="<%= liClass %>">
                <% if item.isEnabled(): %>
                    <a href="<%= item.getURL() %>">
                        <%= item.getTitle() %>
                    </a>
                <% end %>
                <% else: %>
                    <%= item.getTitle() %>
                <% end %>
            </li>
        <% end %>
        
    <%end%>
<% end %>

<% if not somethingVisible: %>
&nbsp;
<% end %>
</ul>
</div>
</div>