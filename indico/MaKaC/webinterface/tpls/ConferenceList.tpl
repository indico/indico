<% from MaKaC.conference import Conference %>
<div class="eventList">

    % if material:
        <span>
            ${ material }
        </span>
    % endif

    % if numOfEventsInTheFuture > 0:
    <div class="topBar" style="margin-bottom: 10px">
        <div class="content smaller">
            <span id="futureEventsShow">
                There are ${ numOfEventsInTheFuture } events in the <em>future</em>.
                <span class="fakeLink futureEventsLink">Show them.</span>
            </span>
            <span id="futureEventsHide" style="display: none;">
                <span class="fakeLink futureEventsLink">Hide</span> the events in the future (${ numOfEventsInTheFuture })
            </span>
        </div>
    </div>
    <div id="futureEvents" style="display: none;">
        <%include file="ConferenceListEvents.tpl" args="items=futureItems, aw=self_._aw, conferenceDisplayURLGen=conferenceDisplayURLGen"/>
    </div>
    % endif
    <div>
        <%include file="ConferenceListEvents.tpl" args="items=presentItems, aw=self_._aw, conferenceDisplayURLGen=conferenceDisplayURLGen"/>
    </div>

    % if numOfEventsInThePast > 0:
    <div id="pastEvents"></div>

    <div class="topBar">
        <div class="content smaller">
            <span id="pastEventsText">
                <span id="pastEventsShow" class="pastEventsControl">
                    There are ${ numOfEventsInThePast } events in the <em>past</em>.
                    <span class="fakeLink pastEventsLink">Show them.</span>
                </span>
                <span id="pastEventsHide" class="pastEventsControl" style="display: none;">
                    <span class="fakeLink pastEventsLink">Hide</span> the events in the past (${ numOfEventsInThePast })
                </span>
                <span id="loadingPast" class="loadingPast"><em>fetching past events...</em></span>
            </span>
        </div>
    </div>
    % endif
</div>

<script type="text/javascript">
    <!-- the following line is left in case we want to go back to the old implementation of the language selector -->
    <!--$E('tzSelector').set(IndicoUI.Widgets.timezoneSelector('${ urlHandlers.UHResetSession.getURL() }'));-->

    // Future events
    % if numOfEventsInTheFuture > 0:
    $('.futureEventsLink').click(function() {
        var fe = $('#futureEvents');
        if (fe.is(':visible')) {
            $('#futureEventsShow').show();
            $('#futureEventsHide').hide();
            fe.slideUp('medium');
        }
        else {
            $('#futureEventsHide').show();
            $('#futureEventsShow').hide();
            fe.slideDown('medium');
        }

    });
    % endif

    // Past events
    % if numOfEventsInThePast > 0:
    var numOfEventsInThePast = ${ numOfEventsInThePast };

    function setShowPastEventsForCateg(show){
        indicoRequest('category.setShowPastEventsForCateg', {
            categId: '${ categ.getId() }',
            showPastEvents: show
        }, function() { });
    }

    $('.pastEventsLink').click(function() {
        if (numOfEventsInThePast) {
            // We need to fetch the events
            setShowPastEventsForCateg(true);
            fetchPastEvents();
        }
        else {
            if ($('#pastEvents').is(':visible')) {
                $('#pastEvents').hide();
                $('#pastEventsHide').hide();
                $('#pastEventsShow').show();
                setShowPastEventsForCateg(false);
            }
            else {
                $('#pastEvents').show();
                $('#pastEventsHide').show();
                $('#pastEventsShow').hide();
                setShowPastEventsForCateg(true);
            }
        }
    });

    function fetchPastEvents() {
        $('#loadingPast').show();
        $('.pastEventsControl').hide();
        indicoRequest('category.getPastEventsList', {
            categId: '${ categ.getId() }',
            lastIdx: numOfEventsInThePast
        }, function(result, error){
            if (result) {
                numOfEventsInThePast -= result.num;
                $.each(result.events, function(i, month) {
                    var id = 'eventList-' + month.year + '-' + month.month;
                    var eventListUL = $('#' + id);
                    if(!eventListUL.length) {
                        eventListUL = $('<ul/>', {id: id});
                        eventListUL.appendTo('#pastEvents').before($('<h4/>').html(month.title));
                    }
                    eventListUL.append($('<div/>').html(month.events.join('')).children());
                });
                if(numOfEventsInThePast > 0) {
                    fetchPastEvents();
                }
                else {
                    $('#loadingPast').hide();
                    $('#pastEventsHide').show();
                }
            }
        });
    }
    % if showPastEvents:
        fetchPastEvents();
    % endif

    % endif

</script>
