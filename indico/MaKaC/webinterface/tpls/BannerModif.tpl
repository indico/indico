<%!

arrowImage = systemIcon( "breadcrumbArrow" )
%>
<div class="path" style="margin-bottom: 25px;">
<table border="0">
<tbody>
    <tr>
        <td align="left" valign="bottom">
             <div class="groupTitleNoBorder" style="letter-spacing: normal; font-style: italic; font-size: 14pt; padding: 0 5px 3px 0; margin:0;">
                <% if type != "": %><%= type %>:<%end%>
            </div>
        </td>
        <td>
            <div class="groupTitleNoBorder" style="letter-spacing: normal; padding: 0;  margin:0;">
                <%= title %>
            </div>
        </td>
    </tr>



<% if len(path) > 0: %>

    <tr>
        <td align="right" valign="top"><span style="padding-right: 5px"><%= _("Go back to:")%></td>
        <td>
        <div style="color: #444;">

            <% for i in range(0, len(path)): %>

                <% object = path[i] %>

                <% if i > 0: %>
                    <img src="<%= arrowImage %>" />
                <% end %>

                <a href="<%= object["url"] %>"><%= object["title"] %></a>
                <%if object.has_key("type"):%>
                <em>
                    (<%= object["type"] %>)
                </em>
                <%end%>
            <% end %>

        </div>
    </td>
</tr>

<% end %>

</tbody>
</table>

</div>


