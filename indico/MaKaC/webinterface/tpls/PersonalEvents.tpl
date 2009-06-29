
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

<h1 class="categorytitle"><%= _("My Indico")%></h1>

<div id="myEventsContainer">
	<!-- Generated DOM Tree -->
</div>



<script type="text/javascript">
	window.onload = function()
						{
							var events = new MyEventsList('myEvents', -1, -1, $('myEventsContainer'), 10);
						};
	
</script>
