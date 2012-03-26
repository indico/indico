<div id="section-<%= section.id %>" class="<%= classes.section %>" >
    <div class="<%= classes.header %>">
        <div class="<%= classes.title %>"><%= section.title %></div>
        <% if ( section.id != "reasonParticipation" && section.id != "furtherInformation") { %>
            <div class="<%= classes.description %>"><%= section.description %></div>
        <% } %>
    </div>

    <!-- further information form -->
    <% if ( section.id == "furtherInformation" ) { %>
        <div class="<%= classes.content %>">
            <div>
                <p class="<%= classes.text %>"><%= section.content %></p>
            </div>
        </div>

    <!-- Participation reason form -->
    <% } else if ( section.id == "reasonParticipation" ) { %>
        <div class="<%= classes.content %>">
            <div>
                <p class="<%= classes.text %>"><%= section.description %></p>
            </div>
            <textarea name="reason" rows="4" cols="80"></textarea>
        </div>

    <!-- session form -->
    <% } else if ( section.id == "sessions" ) { %>
        <div class="<%= classes.content %>">
            <% if ( section.type == "2priorities" ) { %>
            <table>
                <tr>
                    <td>
                        <span><%= $T('Select your preferred choice') %></span>
                        <span class="regFormMandatoryField">*</span>
                    </td>
                    <td class="regFormSectionLeftSpacing1">
                        <select id="session1" name="session1" required>
                            <option value="" selected=""><%= $T('--Select a session--') %></option>
                            <% _.each(section.items, function(item) { %>
                                <option value="<%= item.id %>"><%= item.caption %></option>
                            <% }); %>
                        </select>
                    </td>
                </tr>
                <tr>
                    <td>
                        <span><%= $T('Select your second choice') %></span>
                        <span class="regFormItalic">(Optional)</span>
                    </td>
                    <td class="regFormSectionLeftSpacing1">
                        <select id="session2" name="session2">
                            <option value="nosession" selected=""><%= $T('--Select a session--') %></option>
                            <% _.each(section.items, function(item) { %>
                                <option value="<%= item.id %>"><%= item.caption %></option>
                            <% }); %>
                        </select>
                    </td>
                </tr>
            </table>
            <% } else { %>
            <table>
                <tr>
                    <td class="regFormSectionLeftSpacing1" colspan="3">
                        <% _.each(section.items, function(item) { %>
                            <input class="<% if(item.billable){ print(classes.billable);} %>" type="checkbox" name="sessions" value="<%= item.id %>" /><%= item.caption %>
                                <% if (item.billable) { %>
                                    <span class="<%= classes.price %>"><%= item.price %></span>&nbsp;<span class="<%= classes.currency %>"></span>
                                <% } %>
                                <br>
                        <% }); %>
                    <td>
                </tr>
            </table>
            <% } %>
        </div>

     <!-- accommodation form -->
     <% } else if ( section.id == "accommodation" ) { %>
        <div class="<%= classes.content %>">
            <table>
                <tr>
                    <td>
                        <table>
                            <tr>
                                <td align="left"><span><%= $T('Arrival date') %></span>&nbsp;<span class="regFormMandatoryField">*</span>
                                </td>
                                <td align="left"  class="regFormPadding1">
                                    <select id="arrivalDate" name="arrivalDate" required>
                                        <option value="" selected=""><%= $T('--select a date--') %></option>
                                         <% _.each(section.arrivalDates , function (date) { %>
                                        <option value="<%= date[0] %>"><%= date[1] %></option>
                                        <% }); %>
                                    </select>
                                </td>
                            </tr>
                            <tr>
                                <td align="left"><span>Departure date</span>&nbsp;<span class="regFormMandatoryField">*</span>
                                </td>
                                <td align="left"  class="regFormPadding1">
                                    <select id="departureDate" name="departureDate" required>
                                            <option value="" selected=""><%= $T('--select a date--') %></option>
                                            <% _.each(section.departureDates , function (date) { %>
                                            <option value="<%= date[0] %>"><%= date[1] %></option>
                                            <% }); %>
                                    </select>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td>
                        <table>
                            <tbody>
                                <tr>
                                    <td>
                                        <span id="accommodationTypeLabel" class="regFormSubGroupTitle"><%= $T('Select your accommodation') %></span>
                                        <span class="regFormMandatoryField">*</span>
                                    </td>
                                </tr>
                                <% _.each(section.items , function (item) { %>
                                    <tr>
                                        <td align="left" class="regFormSectionLeftSpacing1">
                                            <% if ( item.cancelled ) { %>
                                                <% var attributes = "disabled" %>
                                            <% } else if ( item.placesLimit != 0 &&  item.noPlacesLeft == 0 ) { %>
                                                <% var attributes = "disabled" %>
                                            <% } else { %>
                                                <% var attributes = "required" %>
                                            <% } %>
                                            <input type="radio" id="<%= item.id %>" class="<% if(item.billable){ print(classes.billable);} %>" name="accommodation_type" value="<%= item.id %>" <%= attributes %> />
                                            <%= item.caption %>

                                            <% if ( item.cancelled ) { %>
                                                <font color="red"> <%= $T('(not available at present)') %></font>
                                            <% } else if ( item.placesLimit != 0 &&  item.noPlacesLeft == 0 ) { %>
                                                <font color="red"> <%= $T('(no places left)') %></font>
                                            <% } else if ( item.placesLimit != 0 ) { %>
                                                <font color="green" style="font-style:italic;"><%= $T('[{0} place(s) left]').format(item.noPlacesLeft) %></font>
                                            <% } %>
                                        </td>
                                        <td align="right" style="padding-left:20px;">
                                            <% if ( item.billable ) { %>
                                                <%= $T('{0} {1} per night').format('<span class=' + classes.price + '>' + item.price + '</span>', '<span class=' + classes.currency + '></span>') %>
                                            <% } %>
                                        </td>
                                    </tr>
                                <% }); %>
                        </table>
                    </td>
                </tr>
            </table>
        </div>

    <!-- social events form -->
    <% } else if ( section.id == "socialEvents" ) { %>
    <div class="<%= classes.content %>">
        <table>
            <tr>
                <td align="left" colspan="3" class="regFormSubGroupTitle" style="padding-bottom:20px"><%= section.introSentence %></td>
            </tr>
                <% _.each(section.items, function(item) { %>
                <tr>
                <% if ( item.cancelled ) { %>
                     <td class="regFormSectionLeftSpacing1">
                        <b>-</b> <%= item.caption %> <font color="red">(<%= item.cancelledReason %>)</font>
                     </td>
                <% } else if ( item.placesLimit != 0 &&  item.noPlacesLeft == 0 ) { %>
                    <td class="regFormSectionLeftSpacing1">
                        <% if ( section.selectionType == "multiple" ) { %>
                            <input type="checkbox" name="socialEvents" value="<%= item.id %>" disabled/><%= item.caption %>&nbsp;&nbsp;
                        <% } else { %>
                            <input type="radio" name="socialEvents" value="<%= item.id %>" disabled/><%= item.caption %>&nbsp;&nbsp;
                        <% } %>
                        <font color="red"><%= $T('(no places left)') %></font>
                     </td>
                <% } else { %>
                    <td class="regFormSectionLeftSpacing1">
                        <% if ( section.selectionType == "multiple" ) { %>
                            <input type="checkbox" class="<% if(item.billable){ print(classes.billable);} %>" name="socialEvents" value="<%= item.id %>"/><%= item.caption %>&nbsp;&nbsp;
                        <% } else { %>
                            <input type="radio" class="<% if(item.billable){ print(classes.billable);} %>" name="socialEvents" value="<%= item.id %>"/><%= item.caption %>&nbsp;&nbsp;
                        <% } %>
                    </td>
                    <td>
                        <select name="places-<%= item.id %>">
                            <% if (item.placesLimit != 0) { %>
                                <% var maxReg = Math.min(item.maxPlacePerRegistrant,item.noPlacesLeft) %>
                            <% } else { %>
                                <% var maxReg = item.maxPlacePerRegistrant %>
                            <% } %>
                            <% for (i = 1; i <= maxReg; i++) { %>
                                <option value="<%= i %>" ><%= i %></option>
                            <% } %>
                        </select>
                        <% if (item.placesLimit != 0) { %>
                            <span class="placesLeft"><%= $T('[{0} place(s) left]').format(item.noPlacesLeft) %></span>
                        <% } %>
                    </td>
                    <% if ( item.billable ) { %>
                        <td align="right">
                            <span class="<%= classes.price %>"><%= item.price %></span>&nbsp;<span class="<%= classes.currency %>"></span>
                            <% if (item.isPricePerPlace ) { print('per place'); }%>
                        </td>
                    <% } %>
                <% } %>

                </tr>
                <% }); %>
        </table>
    </div>

    <!-- General form -->
    <% } else { %>
    <div class="<%= classes.content %> <%= classes.contentIsDragAndDrop %>">
        <% for (var j = 0; j < section.items.length; j++) { %>
            <% var field = section.items[j]; %>
            <%= fields.render(field, section.id) %>
         <% } %>
    </div>
    <% } %>
</div>