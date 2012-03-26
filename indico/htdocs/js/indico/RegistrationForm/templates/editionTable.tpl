<script type="text/template" id="table">
<table>
    <thead>
        <tr role="rowheader">
            <% if ( config.actions.indexOf("sortable") > -1 ) { %>
                <th></th>
            <% } %>
            <% _.each(config.colNames, function(el, ind){ %>
                <th style="width: <%= config.colModel[ind].width %>px;"><%= el %></th>
            <% }); %>
        </tr>
    </thead>
</table>
</script>

<script type="text/template" id="row">
<tbody>
    <tr role="row" id="<%= item.id %>">
        <% if ( config.actions.indexOf("sortable") > -1 ) { %>
        <td>
            <span class="ui-icon ui-icon-arrowthick-2-n-s"></span>
        </td>
        <% } %>
        <% _.each(config.colModel, function (el, el_ind){ %>
            <td role="gridcell" style="text-align: <%= el.align %> ;" name="<%= el.name %>" title="<%= item[el.index] %>">
                <% if ( el.editable == undefined || el.editable == false ) { %>
                    <%= item[el.index] %>
                <% } else if ( el.edittype == "text" || el.edittype == undefined ) { %>
                    <input type="text" size="<%= el.editoptions.size %>" maxlength="<%= el.editoptions.maxlength %>" name="<%= el.name %>" class="editable" value="<%= item[el.index] %>">
                <% } else if ( el.edittype == "bool_select"  ) { %>
                    <select name="<%= el.name %>" size="1" class="editable">
                        <% var selected = el.defaultVal; %>
                        <% if ( ! _.isUndefined(item[el.index]) ) { selected = item[el.index]; } %>
                        <option role="option" value="true"  <% if (selected)  { print("SELECTED"); } %> ><%= $T("yes") %></option>
                        <option role="option" value="false" <% if (!selected) { print("SELECTED"); } %> ><%= $T("no") %></option>
                    </select>
                <% } else if ( el.edittype == "radio" ) { %>
                    <input type="radio" name="<%= el.name %>"/>
                <% } %>
            </td>
        <% }); %>
        <% if ( config.actions.indexOf("remove") > -1 ) { %>
        <td>
            <button class="actionTrash"><%= $T("Remove") %></button>
        </td>
        <% } %>
        <% _.each( config.actions, function(action) { %>
            <% if (_.isArray(action) ){%>
                <td>
                    <button ref="<%= action[1] %>" class="actionTabSwitch ui-button ui-widget ui-state-default ui-corner-all ui-button-icon-only" role="button" aria-disabled="false" title="<%= action[0] %>">
                        <span class="ui-button-icon-primary ui-icon <%= action[2] %>"></span>
                        <span class="ui-button-text">"<%= action[0] %></span>
                    </button>
                </td>
            <% } %>
        <% }); %>
    </tr>
</tbody>
</script>
