<div class="tabbable tabs-left">
    <ul class="nav nav-tabs">
        <li class="active">
            <a data-toggle="tab" id="tab-options" ref="#div-options"><%= $T('Options') %></a>
        </li>
        <% if (field.input == "radio") { %>
        <li>
            <a data-toggle="tab" id="tab-editItems" ref="#div-editItems"><%= $T('Edit items') %></a>
        </li>
        <% } %>
    </ul>
    <div class="tab-content regFormDialogTabContent">
        <div class="tab-pane active" id="div-options">
            <form id="optionsForm">
            <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('caption') %></label>
                <input type="text" name="caption" id="input01" size="30" value="<%= field.caption %>" required>
                <% if (field.mandatory) { var status = "CHECKED" } %>
                <% if (_.indexOf(field.lock, "mandatory") > -1) { status  = status +" DISABLED" } %>
                <input type="checkbox" name="mandatory" id="input02" <%= status %> > <%= $T('Mandatory') %>
           </div>

           <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('description') %></label>
                <textarea id="descriptionEdit" name="description" cols="40" rows="5"><%= any(field.description,'') %></textarea>
           </div>

           <% if (field.input == "telephone" || field.input == "text" ) { %>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('size in char') %></label>
                <input name="length" type="number" size="20" min="5" max="60" value="<% if (field.values.length != 'undefined') {print(field.values.length);}%>">
                <span><%= $T("(Must be between 5 and 60)") %></span>
           </div>
           <% } %>

           <% if ( field.input == "textarea" ) { %>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('number of columns') %></label>
                <input name="numberOfColumns" type="number" min=1 size="20" value="<%= any(field.values.numberOfColumns,'') %>">
           </div>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('number of rows') %></label>
                <input name="numberOfRows" type="number" min=1 size="20" value="<%= any(field.values.numberOfRows,'') %>">
           </div>
           <% } %>

           <% if ( field.input == "number" ) { %>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('minimum value') %></label>
                <input name="minValue" type="number" size="20" value="<%= any(field.values.minValue,'') %>">
           </div>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('row length') %></label>
                <input name="numberOfRows" type="number" min=0 size="20" value="<%= any(field.values.length,'') %>">
           </div>
           <% } %>

           <% if (field.input == "yesno" || field.input == "checkbox") { %>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('places limit') %></label>
                <input name="placesLimit" type="number" size="20" min=0 value="<%= any(field.placesLimit,'') %>">
                <span><%= $T("(0 for unlimited)") %></span>
           </div>
           <% } %>

           <% if (field.input == "yesno" || field.input == "number" || field.input == "label" || field.input == "checkbox" ) { %>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('Billable') %></label>
                <input type="checkbox" name="billable" value="true" <% if(field.billable){print('checked')} %> >
           </div>
           <% } %>

           <% if (field.input == "yesno" || field.input == "number" || field.input == "label" || field.input == "checkbox" ) { %>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('price') %></label>
                <input type="number" min=0 name="price" class="input-xlarge" id="input01" size="20" value="<%= any(field.price,'') %>">
                <% if (field.input == "number" ) { %>
                    <span><%= $T("(price multiplied with entered number)") %></span>
                <% } %>
           </div>
           <% } %>

           <% if (field.input == "radio") { %>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('default item') %></label>
                <select id="defaultItem" name="defaultItem" >
                    <option value=""><%= $T('none') %></option>
                    <% _.each(field.values.radioitems, function(el){ %>
                        <option value="<%= el.caption %>" <% if (field.values.defaultItem == el.caption){print("SELECTED")} %> ><%= el.caption %></option>
                    <% }); %>
                </select>
                 <span><%= $T("(Only available for input type : drop down menu)") %></span>
           </div>
           <% } %>

           <% if (field.input == "radio") { %>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('input type') %></label>
                <select id="inputType" name="inputType" >
                    <option value="dropdown" <% if (field.values.inputType == 'dropdown'){print("SELECTED")} %> ><%= $T('drop down menu') %></option>
                    <option value="radiogroup" <% if (field.values.inputType == 'radiogroup'){print("SELECTED")} %> ><%= $T('radio group') %></option>
                </select>
           </div>
           <% } %>

           <% if (field.input == "date") { %>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption"><%= $T('Date format') %></label>
                <select id="dateFormat" name="dateFormat" >
                    <% if (_.isEmpty(field.values.displayFormats)) { %>
                        <option value="%d/%m/%Y %H:%M" selected="selected">DD/MM/YYYY hh:mm</option>
                        <option value="%d.%m.%Y %H:%M">DD.MM.YYYY hh:mm</option>
                        <option value="%m/%d/%Y %H:%M">MM/DD/YYYY hh:mm</option>
                        <option value="%m.%d.%Y %H:%M">MM.DD.YYYY hh:mm</option>
                        <option value="%Y/%m/%d %H:%M">YYYY/MM/DD hh:mm</option>
                        <option value="%Y.%m.%d %H:%M">YYYY.MM.DD hh:mm</option>
                        <option value="%d/%m/%Y">DD/MM/YYYY</option>
                        <option value="%d.%m.%Y">DD.MM.YYYY</option>
                        <option value="%m/%d/%Y">MM/DD/YYYY</option>
                        <option value="%m.%d.%Y">MM.DD.YYYY</option>
                        <option value="%Y/%m/%d">YYYY/MM/DD</option>
                        <option value="%Y.%m.%d">YYYY.MM.DD</option>
                        <option value="%m/%Y">MM/YYYY</option>
                        <option value="%m.%Y">MM.YYYY</option>
                        <option value="%Y">YYYY</option>
                     <% } else { %>
                        <% _.each(field.values.displayFormats, function(el){ %>
                        <option value="<%= el[0] %>" <% if (el[0] == field.values.dateFormat){print("SELECTED")} %> ><%= el[1] %></option>
                        <% }); %>
                     <% } %>
                </select>
           </div>
           <% } %>
            <input type="submit" style="display:none;" value="submit" id="form-opt-validate">
           </form>
        </div>
        <div class="tab-pane" id="div-editItems">
            <button id="addButton" class="addItem"><%= $T('Create new item') %></button>
            <button id="sortItem"  class="sortItem"><%= $T('Sort alphabetically') %></button>
            <div id="editionTable" style="margin-right:20px;margin-top:20px;"></div>
        </div>
    </div>
</div>
