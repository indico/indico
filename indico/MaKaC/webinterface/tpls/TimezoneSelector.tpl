<a id="timezoneSelectorLink" class="dropDownMenu fakeLink" style="display: inline-block;">
    ${ ActiveTimezoneDisplay }
</a>

<script type="text/javascript">
var timezoneSelectorLink = $E('timezoneSelectorLink');

var tzSelector = new TimezoneSelector(
        timezoneSelectorLink,
        '${ ActiveTimezone }',
        '${ ActiveTimezoneDisplay }',
        ${"'"+ currentUser.getTimezone() +"'" if currentUser else "null"},
        ${"'"+ currentUser.getDisplayTZMode() +"'" if currentUser else "null"},
        '${ urlHandlers.UHResetSession.getURL() }'
);

$("#timezoneSelectorLink").qtip({

    style: {
        width: '300px',
        classes: 'qtip-rounded qtip-shadow qtip-popup qtip-timezone',
        tip: {
            corner: true,
            width: 20,
            height: 15
        }
    },
    position: {
        my: 'top center',
        at: 'bottom center'
    },
    content: function(api){
        return $(tzSelector.getContent().dom);
        },
    show: {
        event: "click",
        effect: function() {
            $(this).fadeIn(300);
        }
    },
    hide: {
        event: 'unfocus click',
        fixed: true,
        effect: function() {
            $(this).fadeOut(300);
        }
    }
});

</script>

