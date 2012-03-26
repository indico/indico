<script type="text/template" id="edit-dialog">
<div class="tabbable tabs-left">
    <ul class="nav nav-tabs">
        <% _.each(section.tabs, function(tab) { %>
        <li>
            <a data-toggle="tab" id="tab-<%= tab.id %>" ref="#div-<%= tab.id %>"><%= tab.name %></a>
        </li>
        <% }); %>
    </ul>
    <div class="tab-content regFormDialogTabContent" style="width: <%= contentWidth %>px; overflow: hidden; white-space: nowrap;">
        <% _.each(section.tabs, function(tab) { %>
        <div class="tab-pane" id="div-<%= tab.id %>">
            <%= getTabHtml(tab) %>
        </div>
        <% }); %>
    </div>
</div>
</script>

<script type="text/template" id="config-socialEvents">
<form>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaption"><%= $T('Selection type') %></label>
        <select name="selectionType">
            <option value="unique" <% if (selectionType == "unique") {print("selected");} %> ><%= $T('Unique choice') %></option>
            <option value="multiple" <% if (selectionType == "multiple") {print("selected");} %> ><%= $T('Multiple choice') %></option>
        </select>
    </div>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaption"><%= $T('Introduction sentence') %></label>
        <textarea id="descriptionEdit" name="introSentence" cols="40" rows="6"><%= introSentence %></textarea>
     </div>
</form>
</script>

<script type="text/template" id="config-sessions">
<form>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaption" style="width : 180px"><%= $T('Type of sessions\' form') %></label>
        <select name="type">
            <option value="2priorities" <% if (type == "2priorities") {print("selected");} %> ><%= $T('2 choices') %></option>
            <option value="all" <% if (type == "all") {print("selected");} %> ><%= $T('multiple') %></option>
        </select>
    </div>
    <span> <%= $T('How many sessions the registrant can choose.') %>
        <br> <%= $T('Please note that <b>billing</b> is <b>not possible</b> when using <b>2 choices</b>') %>
    </span>
</form>
</script>

<script type="text/template" id="addSession-sessions">
<form>
    <% _.each(sessions, function (el, ind) { %>
        <input type="checkbox" name="session" value="<%= el.id %>"><%= el.caption %></input><br>
    <% }); %>
</form>
</script>

<script type="text/template" id="editionTable-sessions">
<div id="editionTable" class="regFormDialogEditionTable"></div>
</script>

<script type="text/template" id="editionTable-socialEvents">
<div class="regFormEditLine" style="margin-bottom: 20px;">
    <button id="addButton" class="addItem"><%= $T('Add a new social event') %></button>
</div>
<div id="editionConfigTable" class="regFormDialogEditionTable"></div>
</script>

<script type="text/template" id="editionTable-accommodation">
<div class="regFormEditLine" style="margin-bottom: 20px;">
    <button id="addButton" class="addItem"><%= $T('Add a new accommodation') %></button>
</div>
<div id="editionTable" class="regFormDialogEditionTable"></div>
</script>

<script type="text/template" id="cancelEvent-socialEvents">
    <div id="editionCanceledTable" class="regFormDialogEditionTable"></div>
</script>

<script type="text/template" id="cancelEvent-socialEventsOLD">
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaptionLine"><%= $T('Cancellation of the "{0}" social event').format('<span id="cancelEventCaption"></span>') %></label>
    </div>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaption"><%= $T('Reason') %></label>
         <textarea id="cancelledReason" cols="40" rows="6"></textarea>
    </div>
    <div class="regFormEditLine" style="margin-bottom: 20px;">
        <button id="cancelEvent"><%= $T('Cancel Event') %></button>
        <button id="undoCancelEvent"><%= $T('Undo') %></button>
    </div>
</script>

<script type="text/template" id="config-accommodation">
<form>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaptionLine"><%= $T('Arrival dates (offset)') %></label>
        <%= $T('event start date offset:') %><input type="text" name="aoffset1" size="2" value="<%= arrivalOffsetDates[0] %>"><%= $T('days') %>-&gt;
        <%= $T('event end date offset:') %><input type="text" name="aoffset2" size="2" value="<%= arrivalOffsetDates[1] %>"><%= $T('days') %>
    </div>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaptionLine"><%= $T('Departure dates (offset)') %></label>
        <%= $T('event start date offset:') %><input type="text" name="doffset1" size="2" value="<%= departureOffsetDates[0] %>"><%= $T('days') %> -&gt;
        <%= $T('event end date offset:') %><input type="text" name="doffset2" size="2" value="<%= departureOffsetDates[1] %>"><%= $T('days') %>
    </div>
</form>
</script>

