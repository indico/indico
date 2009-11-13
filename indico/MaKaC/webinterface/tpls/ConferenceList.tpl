<%! 
def sortAndReturn(list):
	list.sort()
	list.reverse()
	return list
%>

<% from MaKaC.conference import Conference %>
<div class="eventList">

	<% if material: %>
		<span>
			<%= material %>
		</span>
	<% end %>
    
    <% if numOfEventsInTheFuture > 0: %>
    <div class="topBar" style="margin-bottom: 10px">
        <div class="content smaller"><span id="futureEventsText">There are <%= numOfEventsInTheFuture %> more events in the <em>future</em>. <span class='fakeLink' onclick='toogleFutureEvents();'>Show them.</span></span></div>
    </div>
    <div id="futureEvents" style="visibility: hidden; overflow:hidden;">
        <% includeTpl('ConferenceListEvents', items=futureItems, aw=self._aw, conferenceDisplayURLGen=conferenceDisplayURLGen) %>
                
    </div>
    <% end %>
    <div>
    <% includeTpl('ConferenceListEvents', items=presentItems, aw=self._aw, conferenceDisplayURLGen=conferenceDisplayURLGen) %>
    </div>

    <% if numOfEventsInThePast > 0: %>    
    <div id="pastEvents" style="display:none"></div>

    <div class="topBar">
        <div class="content smaller"><span id="pastEventsText">There are <%= numOfEventsInThePast %> more events in the <em>past</em>. <span class='fakeLink' onclick='tooglePastEvents();'>Show them.</span><span id="loadingPast" class="loadingPast"><em>fetching past events...</em></span></span></div>
    </div>
    <% end %>

</div>

<script type="text/javascript">
    <!-- the following line is left in case we want to go back to the old implementation of the language selector -->
    <!--$E('tzSelector').set(IndicoUI.Widgets.timezoneSelector('<%= urlHandlers.UHResetSession.getURL() %>'));-->

    <% if numOfEventsInTheFuture > 0: %>
    var futureSwitch = false;
    var futureEvents = $E("futureEvents");
    var futureEventsDivHeight=futureEvents.dom.offsetHeight;
    futureEvents.dom.style.height = '0';
    //futureEvents.dom.style.visibility = "visible";
    futureEvents.dom.style.opacity = "0";
    function toogleFutureEvents() {
        if (futureSwitch) {
            IndicoUI.Effect.slide("futureEvents", futureEventsDivHeight); 
            $E("futureEventsText").dom.innerHTML = "There are <%= numOfEventsInTheFuture %> more events in the <em>future</em>. <span class='fakeLink' onclick='toogleFutureEvents()'>Show them.</a>";
        }else {
            IndicoUI.Effect.slide("futureEvents", futureEventsDivHeight); 
            $E("futureEventsText").dom.innerHTML = '<span class="fakeLink" onclick="toogleFutureEvents()">Hide</span> the events in the future (<%= numOfEventsInTheFuture %>).';
        }
        futureSwitch = !futureSwitch;
    } 
    <%end%>

    <% if numOfEventsInThePast > 0: %>
    var callDone = false;
    var pastSwitch = false;
    function tooglePastEvents() {
        if (!callDone) {
            $E("loadingPast").dom.style.display = "inline";
            fetchPastEvents()
        }else {
            if (pastSwitch) {
                $E("pastEvents").dom.style.display = "none";
                $E("pastEventsText").dom.innerHTML = "There are <%= numOfEventsInThePast %> more events in the <em>past</em>. <span class='fakeLink' onclick='tooglePastEvents()'>Show them.</a>";
            }else {
                $E("pastEvents").dom.style.display = "inline"; 
                $E("pastEventsText").dom.innerHTML = '<span class="fakeLink" onclick="tooglePastEvents()">Hide</span> the events in the past (<%= numOfEventsInThePast %>).';
            }
            pastSwitch = !pastSwitch;
        }
    }

    function fetchPastEvents() {
        indicoRequest('category.getPastEventsList',
                {
                    categId: '<%= categ.getId() %>',
                    fromDate: '<%= oldestMonthDate.strftime("%Y/%m/%m %H:%M") %>'
                },
                function(result, error){
                    if (!error) {
                        callDone = true;
                        $E("pastEvents").dom.innerHTML = result;
                        $E("loadingPast").dom.style.display = "none";
                        tooglePastEvents();
                    }
                }
            )
    }

    <% end %>
    
</script>