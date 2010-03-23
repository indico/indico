<% if CanBeNotified: %>
<!-- // If this booking in particular cannot be notified of date changes any more, we disable the checkbox -->
<div style="margin-left:50px; padding-bottom:10px;">
    <input type="checkbox" id="dateSyncCheckBox" name="notifyOnDateChanges" value="notifyOnDateChanges" checked />
    <label for="dateSyncCheckBox" class="normal"><%= _("Keep booking synchronized with event") %></label>
    <img id="dateSyncHelpImg" src="<%= systemIcon('help')%>" style="margin-left:5px; vertical-align:middle;" />
</div>
<% end %>

<div style="margin-left:50px">
    <input type="checkbox" id="hiddenCheckBox" name="hidden" value="hidden"></input>
    <label for="hiddenCheckBox" class="normal"><%= _("Keep this booking hidden") %></label>
    <img id="hiddenHelpImg" src="<%= systemIcon('help')%>" style="margin-left:5px; vertical-align:middle;" />
</div>
