<a id="timezoneSelectorLink" class="dropDownMenu" style="display: inline-block;" href="#">
    ${ ActiveTimezoneDisplay }
</a>

<script type="text/javascript">

var timezoneSelectorLink = $E('timezoneSelectorLink');
var tzSelector = null;

timezoneSelectorLink.observeClick(function() {
    tzSelector = new TimezoneSelector(
            timezoneSelectorLink,
            '${ ActiveTimezone }',
            '${ ActiveTimezoneDisplay }',
            ${"'"+ currentUser.getTimezone() +"'" if currentUser else "null"},
            ${"'"+ currentUser.getDisplayTZMode() +"'" if currentUser else "null"},
            '${ urlHandlers.UHResetSession.getURL() }'
    );
});

</script>

