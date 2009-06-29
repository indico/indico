<%
r = bar.forReservation

left = int( 1.0 * ( (bar.startDT.hour-START_H) * 60 + bar.startDT.minute ) / (24*60) * DAY_WIDTH_PX  )
diff = ( bar.endDT.hour - bar.startDT.hour ) * 60 + ( bar.endDT.minute - bar.startDT.minute )
width = int( 1.0 * diff / (24*60) * DAY_WIDTH_PX ) - 1
id = "barDiv_" + str(room.id) + "_" + str( dayDT ) + "_" + str( bar.startDT.time() )

resvInfo = "%s  -  %s<br />%s<br />%s" % (verbose_t( bar.startDT.time() ), verbose_t( bar.endDT.time() ), escapeAttrVal( r.bookedForName ), escapeAttrVal( r.reason ) )
resvUrl = bookingDetailsUH.getURL( r )
%>
<%
if bar.type == Bar.UNAVAILABLE:
    barClass = 'barUnaval'
%>
<% end %>

<%
if bar.type == Bar.CANDIDATE: 
    barClass = 'barCand'
    resvUrl = "#conflicts"
%>
<% end %>

<% 
if bar.type == Bar.CONFLICT:
    barClass = 'barConf'
%>
<% end %>

<%
if bar.type == Bar.PREBOOKED: 
    barClass = 'barPreB'
%>
<% end %>

<%
if bar.type == Bar.PRECONFLICT: 
    barClass = 'barPreC'
%>
<% end %>

<%
if bar.type == Bar.PRECONCURRENT: 
    barClass = 'barPreConc'
%>
<% end %>


<div id="<%= id %>" class="<%= barClass %>" style="cursor: pointer; width: <%= width %>px; left: <%= left %>px;" onmouseover="domTT_activate(this, event, 'content', '<%= resvInfo %>', 'delay', 100, 'maxWidth', 320, 'styleClass', 'tip' );" onclick="window.location = '<%=resvUrl%>';"></div>