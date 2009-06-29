                    <select id="selectRoom" name="roomName" onchange="roomChanged();">
					    <% for r in roomList: %>
					        
					        <% selected = "" %>
					        <% if r.name == locationRoom: %>
					            <% selected = 'selected="selected"' %>
					        <% end %>

                            <option value="<%= r.name %>" <%= selected %> class="<%=roomClass( r )%>"><%= r.locationName + ": &nbsp; " + r.name %></option>
					    <% end %>
                        
                        <option value="" style="font-weight: bold;">->  <%= _("Other room")%></option>
                    </select>
                     <%= _("Select '<b>Other room</b>' to type in arbitrary name")%>
