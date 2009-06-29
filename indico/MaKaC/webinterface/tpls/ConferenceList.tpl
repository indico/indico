<%! import datetime

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

<% for year in sortAndReturn(items.keys()): %>
	<h3><%= year %></h3>
	<% for month in sortAndReturn(items[year].keys()): %>
		<h4><%= datetime.datetime(year, month, 1).strftime("%B %Y") %></h4>
		<ul>
		<% for day in sortAndReturn(items[year][month].keys()): %>			
			<% for item in sortAndReturn(items[year][month][day].keys()): %>
				<% includeTpl('ConferenceListItem', aw=self._aw, lItem=items[year][month][day][item], conferenceDisplayURLGen=conferenceDisplayURLGen) %>
			<% end %>
		<% end %>
		</ul>
	<% end %>
<% end %>

</div>

<script type="text/javascript">
    <!-- the following line is left in case we want to go back to the old implementation of the language selector -->
    <!--$E('tzSelector').set(IndicoUI.Widgets.timezoneSelector('<%= urlHandlers.UHResetSession.getURL() %>'));-->
</script>