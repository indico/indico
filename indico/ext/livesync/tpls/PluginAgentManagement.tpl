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
        <a href="#" onclick="javascript: editAgent('<%= agentId %>'); return false;">Edit</a> <a href="#" onclick="javascript: deleteAgent('<%= agentId %>'); return false;">Delete</a>
      </td>
</tr>
<% end %>
</table>

<a href="#" onclick="javascript:addAgent(); return false;">Add new agent</a>

<script type="text/javascript">

  var availableTypes = <%= jsonEncode(availableTypes) %>;
  var agentTableData = <%= jsonEncode(agentTableData) %>;
  var agentExtraOptions = <%= jsonEncode(extraAgentOptions) %>;

  function deleteAgent(agentId) {
      if (confirm($T("Are you sure you want to delete agent ") + agentId + "?")) {
          deleteAgentAction(agentId);
      }
  }

  function addAgent() {
      var dialog = new AddAgentDialog(availableTypes, agentExtraOptions);
      dialog.open();
  }

  function editAgent(agentId) {
      var dialog = new EditAgentDialog(availableTypes,
                                       agentExtraOptions[agentTableData[agentId]._type],
                                       agentTableData[agentId]);
      dialog.open();
  }

</script>
