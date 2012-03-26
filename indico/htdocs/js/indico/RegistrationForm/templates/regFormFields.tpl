<script type="text/template" id="itemWrapStd">
<table class="<% if (field.disabled) {print(classes.fieldDisabled)} else {print(classes.field)} %>" id="<%= field.id %>" >
    <tr>
      <td class="regFormCaption">
          <span class="regFormCaption"><%= field.caption %></span>
          <% if (field.mandatory) { %>
                <span class="regFormMandatoryField">*</span>
          <% } %>
      </td>
      <td>
          <%= item %>
      </td>
    </tr>
</table>
</script>

<script type="text/template" id="itemWrapAllRight">
<table class="<% if (field.disabled) {print(classes.fieldDisabled)} else {print(classes.field)} %>" id="<%= field.id %>">
    <tr>
      <td class="regFormCaption">
      </td>
      <td>
          <%= item %>
      </td>
    </tr>
</table>
</script>

<script type="text/template" id="text">
<table>
    <tr>
        <% if (field.values.length != "") { %>
            <td><input id="<%= name %>" type="text" name="<%= name %>" value=""  size="<%= field.values.length %>" <%= attributes %>></td>
         <% } else { %>
            <td><input id="<%= name %>" type="text" name="<%= name %>" value=""  size="60" <%= attributes %>></td>
         <% } %>
    </tr>
    <tr>
        <td colspan="2">
            <span class="inputDescription"><%= field.description %></span>
        </td>
    </tr>
</table>
</script>

<script type="text/template" id="country">
<table>
    <tr>
        <td>
        <select id="<%= name %>" name="<%= name %>" <%= attributes %>>
            <option value=""><%= $T('-- Select a country --') %></option>
            <% _.each(field.values.radioitems, function(el){ %>
                <option value="<%= el.countryKey %>"><%= el.caption %></option>
            <% }); %>
        </select>
    </td>
  </tr>
  <tr>
     <td colspan="2">
        <span class="inputDescription"><%= field.description %></span>
     </td>
  </tr>
</table>
</script>

<script type="text/template" id="radio">
<table>
    <% if (field.values.inputType == "dropdown") { %>
    <tr>
      <td>
        <select name="<%= name %>" <%= attributes %> ">
            <option value=""><%= $T('-- Choose a value --') %></option>
            <% _.each(field.values.radioitems, function(el){ %>
                <% var attributes = '' %>
                <% if ( el.placesLimit != 0 &&  el.noPlacesLeft == 0 ) { %>
                   <% attributes = 'disabled' %>
                <% } else if (field.values.defaultItem == el.caption) { %>
                   <% attributes = 'selected' %>
                <% } %>
                <option value="<%= el.id %>" <%= attributes %> class="<% if(el.isBillable){ print(classes.billable);} %>" ><%= el.caption %></option>
            <% }); %>
        </select>
      </td>
    </tr>
    <% } else { %>
        <% _.each(field.values.radioitems, function(el, ind){ %>
        <tr>
            <% var disabled = false; %>
            <% if ( el.placesLimit != 0 &&  el.noPlacesLeft == 0 ) { %>
                <% disabled = true; %>
            <% } %>
            <td >
                <input type="radio" class="<% if(el.isBillable){ print(classes.billable);} %>" name="<%= name %>" value="<%= el.id %>" <%= attributes %> <% if(disabled){print("DISABLED")} %>/>
            </td>
            <td>
                <%= el.caption %>
            </td>
            <td>
                <% if (el.isBillable && ! disabled) { %>
                    <span class="<%= classes.price %>"><%= el.price %></span>&nbsp;<span class="<%= classes.currency %>"></span>
                <% } %>
            </td>
            <td>
                <% if ( disabled ) { %>
                    <font color="red" style="margin-left:25px;"><%= $T("(no places left)") %></font>
                <% } else if (el.placesLimit != 0) { %>
                    <font color="green" style="font-style:italic; margin-left:25px;"><%= $T('[{0} place(s) left]').format(el.noPlacesLeft) %></font>
                <% } %>
            </td>
        </tr>
        <% }); %>
    <% } %>
    <tr>
        <td colspan="2">
            <span class="inputDescription"><%= field.description %></span>
        </td>

    </tr>
</table>
</script>

<script type="text/template" id="file">
<table>
    <tr>
        <td>
            <div id="attachment<%= name %>" class="existingAttachment">
                <input id="<%= name %>" name="<%= name %>" type="file" <%= attributes %>>
            </div>
        </td>
        <td align="right" valign="bottom"></td>
    </tr>
    <tr>
        <td colspan="2">
            <span class="inputDescription"><%= field.description %></span>
        </td>
    </tr>
</table>
</script>

<script type="text/template" id="radiogroup">
<table>
    <tr>
        <td align="right" colspan="2">
        </td>
    </tr>

    <% _.each(field.values.radioitems, function(el, ind){ %>
    <tr>
        <td>
        </td>
        <td>
            <input type="radio" id="<%= name %>_<%= ind %>" name="<%= name %>" value="<%= el.id %>" <%= attributes %>/><%= el.caption %>
        </td>
    </tr>
    <% }); %>
    <tr>
        <td>
        </td>
        <td colspan="2">
            <span class="inputDescription"><%= field.description %></span>
        </td>
     </tr>
</table>
</script>

<script type="text/template" id="date">
<table>
    <tr>
        <td>
            <span id="<%= name %>_DatePlace">
                <div class="dateField">
                    <input type="text" <%= attributes %> ><img src="<%= imageSrc('calendarWidget') %>">
                </div>
            </span>
            <input type="hidden" value="" name="<%= name %>_Day" id="<%= name %>_Day">
            <input type="hidden" value="" name="<%= name %>_Month" id="<%= name %>_Month">
            <input type="hidden" value="" name="<%= name %>_Year" id="<%= name %>_Year">
            <input type="hidden" value="" name="<%= name %>_Hour" id="<%= name %>_Hour">
            <input type="hidden" value="" name="<%= name %>_Min" id="<%= name %>_Min">
            &nbsp;
            <span class="inputDescription">
                <% _.each(field.values.displayFormats, function(el){ if (el[0]==field.values.dateFormat) { print(el[1]) }}); %>
            </span>
        </td>
        <td align="right">
        </td>
     </tr>
     <tr>
        <td>
            <span class="inputDescription"><%= field.description %></span>
        </td>
     </tr>
</table>
</script>

<script type="text/template" id="number">
<table>
    <tr>
        <td>
            <input type="number" id="<%= name %>" name="<%= name %>" min="<%= field.values.minValue %>" class="<% if(field.billable){ print(classes.billable);} %>" value="<%= field.values.minValue %>" <%= attributes %> onchange="$E('subtotal-<%= name %>').dom.innerHTML = ((isNaN(parseInt(this.value, 10)) || parseInt(this.value, 10) &lt; 0) ? 0 : parseInt(this.value, 10)) * <%= field.price %>;" size="<%= field.values.length %>">
        </td>
        <td align="right">
            &nbsp;&nbsp;<span class="<%= classes.price %>"><%= field.price %></span>&nbsp;<span class="<%= classes.currency %>"></span>
            <span class="regFormSubtotal"><%= $T('Total:') %></span> <span id="subtotal-<%= name %>">0</span>
            &nbsp;<span class="<%= classes.currency %>"></span>
         </td>
     </tr>
     <tr>
        <td colspan="2">
            <span class="inputDescription"><%= field.description %></span>
        </td>
      </tr>
</table>
</script>

<script type="text/template" id="yesno">
<table>
    <tr>
        <td>
            <select id="<%= name %>" name="<%= name %>" <%= attributes %> class="<% if(field.billable){ print(classes.billable);} %>">
                <option value=""><%= $T('-- Choose a value --') %></option>
                <option value="yes"><%= $T('yes') %>&nbsp;
                <% if (field.placesLimit != 0) { %>
                    <%= $T('[ {0} place(s) left]').format(field.noPlacesLeft) %>
                <% } %>
                </option>
                <option value="no"><%= $T('no') %></option>
            </select>
         </td>
         <td align="right">
            <% if (field.billable) { %>
                <span class="<%= classes.price %>"><%= field.price %></span>
                <span class="<%= classes.currency %>"></span>
            <% } %>
         </td>
     </tr>
     <tr>
        <td colspan="2"><span class="inputDescription"><%= field.description %></span></td>
     </tr>
</table>
</script>

<script type="text/template" id="label">
<table class="<%= classes.field %>" id="<%= field.id %>">
    <tr>
        <td colspan="2"><%= field.caption %>
            
            <% if (field.billable) { %>
                &nbsp;&nbsp;&nbsp;
                <span class="<%= classes.price %>"><%= field.price %></span>
                <span class="<%= classes.currency %>"></span>
            <% } %>
        </td>
    </tr>
    <tr>
        <td colspan="2"><span class="inputDescription"><%= field.description %></span></td>
    </tr>
</table>
</script>

<script type="text/template" id="textarea">
<table>
    <tr>
        <td>
            <span class="inputDescription"><%= field.description %></span><br>
            <textarea id="<%= name %>" name="<%= name %>" cols="<%= field.values.numberOfColumns %>" rows="<%= field.values.numberOfRows %>" <%= attributes %>></textarea>
         </td>
    </tr>
</table>
</script>

<script type="text/template" id="checkbox">
<table>
    <tr>
        <td>
            <input type="checkbox" id="<%= name %>" class="<% if(field.billable){ print(classes.billable);} %>" name="<%= name %>" <%= attributes %>>
        </td>
        <td>
        <%= field.caption %>
        </td>
        <td align="right">
            <% if (field.billable) { %>
                <span class="<%= classes.price %>"><%= field.price %></span>
                <span class="<%= classes.currency %>"></span>
            <% } %>
            <% if (field.placesLimit != 0 && field.noPlacesLeft != 0) { %>
                &nbsp;&nbsp;<span class="placesLeft"><%= $T('[{0} place(s) left]').format(field.noPlacesLeft) %></span>
            <% } else if( field.placesLimit != 0 &&  field.noPlacesLeft == 0 ) { %>
                &nbsp;&nbsp;<font color="red"> <%= $T('(no places left)') %></font>
            <% } %>
        </td>
    </tr>
    <tr>
        <td colspan="4">
            <span class="inputDescription"><%= field.description %></span>
        </td>
    </tr>
</table>
</script>

<script type="text/template" id="telephone">
<table>
    <tr>
        <td>
            <input type="text" id="<%= name %>" name="<%= name %>" value="" size="30" <%= attributes %>>&nbsp;
            <span class="inputDescription">(+) 999 99 99 99</span>
        </td>
    </tr>
    <tr>
        <td>
            <span class="inputDescription"><%= field.description %></span>
        </td>
    </tr>
</table>
</script>