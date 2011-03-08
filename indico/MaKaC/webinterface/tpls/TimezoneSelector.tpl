<a id="timezoneSelectorLink" class="dropDownMenu" style="display: inline-block;" href="#">
    <%= ActiveTimezoneDisplay %>
</a>

<script type="text/javascript">

var timezoneSelectorLink = $E('timezoneSelectorLink');
var tzSelector = null;

timezoneSelectorLink.observeClick(function() {
    tzSelector = new TimezoneSelector(
            timezoneSelectorLink,
            '<%= ActiveTimezone %>',
            '<%= ActiveTimezoneDisplay %>',
            <% if currentUser: %>'<%= currentUser.getTimezone() %>'<% end %><% else: %>null<% end %>,
            <% if currentUser: %>'<%= currentUser.getDisplayTZMode() %>'<% end %><% else: %>null<% end %>,
            '<%= urlHandlers.UHResetSession.getURL() %>'
    );
});

</script>

