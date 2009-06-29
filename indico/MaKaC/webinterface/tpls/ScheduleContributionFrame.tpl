<% declareTemplate(newTemplateStyle=True) %>

<div style="overflow: visible; border: 1px solid #DDDDDD; padding: 10px; height: 20px; margin-left: auto; margin-right: auto;">
        
        <div style="float: left;">
            <span style="float: left; margin-right: 5px;">Contribution:</span>
            <form action="<%= handler.getURL(self._conf) %>" method="GET">
                <select name="contribId" onchange="javascript: this.form.submit();">
                    <% for contrib in contribList: %>
                        <option value="<%= contrib.getId() %>"                        
                            <% if self._contrib == contrib: %>
                                selected
                            <% end %>>
                            <%= contrib.getTitle() %>                             
                        </option>
                   <% end %>
                </select>
				<input type="hidden" name="day" value="<%= days %>" />
                <input type="hidden" name="confId" value="<%= self._conf.getId() %>" />
           </form>          
        </div>
        <div style="float: left; padding-left: 50px;">
            <form action="<%= urlHandlers.UHContribModifSchedule.getURL(self._contrib) %>" method="POST" style="display: inline;">
				<input type="hidden" name="day" value="<%= days %>" />
                <input type="submit" class="btn" value="Timetable" />   
            </form>
        </div>
    </div>

<%= body %>
