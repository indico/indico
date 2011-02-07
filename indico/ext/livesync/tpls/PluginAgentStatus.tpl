<h2><%= _("Livesync Status") %></h2>

<% if trackData == None: %>
<em><%= _("There is still no data") %></em>
<% end %>
<% else: %>
<div style="float:left;">
<table class="agentStatusTable" style="margin-top:20px;">
<% lastTS, harvested = None, True %>
<% for ts, dt, nelems, agents in trackData: %>
    <% if ts == lastAgentTS: %>
      <% harvested = False %>
    <% end %>
      <% if ts == 'break': %>
        <tr>
        <td class="timestamp"></td>
        <td class="content break"><%= dt %> <%= _("entrie(s)") %>, <%= nelems %> <%= _("changeset(s)") %> </td>
        <td class="agents"></td>
      <% end %>
      <% else: %>
        <% if lastTS and lastTS != ts - 1 and lastTS != 'break': %>
          <tr class="spacer"><td></td></td><td></td></tr>
        <% end %>
        <tr>
        <td class="timestamp"><%= ts %><div class="small"><%= dt %></div></td>
        <td class="content<% if not harvested: %> notharvested<% end %><% if len(agents) > 0: %> hasagents<% end %>">
            <% if nelems == 0: %>
               (nothing)
            <% end %>
            <% else: %>
               <%= nelems %>&nbsp;<%= _("changeset(s)") %>
            <% end %>
        </td>
        <td class="agents">
          <% if len(agents) > 0: %>
          ⇦
          <% end %>
          <%= ', '.join(agents) %>
        </td>
      <% end %>
   </tr>
   <% lastTS = ts %>
<% end %>
<tr class="downarrows">
<td></td><td>⇩    ⇩</td><td></td>
</tr>
</table>
</div>

<div class="legend">
<ul style="list-style-type:none; padding: 0px; margin: 0px;">
<li>
  <div style="background-color: #F7F3E8;" class="colorSquare"></div>
  <div style="float:left"><%= _("already harvested") %></div></li>
<li>
  <div style="background-color: #EEE;" class="colorSquare"></div>
  <div style="float:left"><%= _("not yet harvested") %></div></li>
</ul>
</div>

<div style="clear: both"></div>

<ul class="infobox">
  <li><label>Current slot:</label> <%= currentTS / granularity %> (<%= currentTS %>)</li>
  <li><label>Time to next slot:</label> <%= (currentTS / granularity + 1) * granularity - currentTS %>s</li>
</ul>


<% end %>
