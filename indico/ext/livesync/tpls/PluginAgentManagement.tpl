<h2>Agents</h2>
<table class="schedTaskList" style="margin-bottom: 20px;">
<tr>
<th>Type</th>
<th>Id</th>
<th>Name</th>
<th>Description</th>
<th>Last result</th>
<th></th>
</tr>
<% for agentId, agent in agents.iteritems(): %>
   <tr>
      <td><%= agent.__class__.__name__ %></td>
      <td><%= agentId %></td>
      <td><%= agent.getName() %></td>
      <td><%= agent.getDescription() %></td>
      <td></td>
      <td>
        <a href="#" onclick="javascript: deleteAgent('<%= agentId %>'); return false;">Delete</a>
      </td>
</tr>
<% end %>
</table>

<a href="#" onclick="javascript:addAgent(); return false;">Add new agent</a>

<script type="text/javascript">

  function deleteAgent(agentId) {
      if (confirm($T("Are you sure you want to delete agent ") + agentId + "?")) {
          window.location.reload();
      }
  }

  function addAgent() {
      var dialog = new AddAgentDialog();
      dialog.open();
  }

</script>
