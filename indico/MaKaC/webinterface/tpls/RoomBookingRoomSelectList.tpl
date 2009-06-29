                    <select id="select_roomNameList" name="locationRoom">
					    <option value="">-------------------</option>
						<% for r in roomList: %>
					        
					        <% selected = "" %>
					        <% if r.name == locationRoom: %>
					            <% selected = 'selected' %>
					        <% end %>

                            <option value="<%= r.name %>" <%= selected %> class="<%=roomClass( r )%>"><%= r.locationName + ": &nbsp; " + r.name %></option>
					    <% end %>
                        
                        
                    </select>                    
