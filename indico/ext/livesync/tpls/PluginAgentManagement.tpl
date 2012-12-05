<h2>Agents</h2>
<table class="schedTaskList" style="margin-bottom: 20px;">
<tr>
<th>Type</th>
<th>Id</th>
<th>Name</th>
<th>Description</th>
<th>Position</th>
<th></th>
</tr>
% for agentId, agent in agents.iteritems():
   <tr>
      <td>${ agent.__class__.__name__ }</td>
      <td>${ agentId }</td>
      <td>${ agent.getName() }</td>
      <td>${ agent.getDescription() }</td>
      <td>
      % if agent.isActive():
      ${ agent.getLastDT() } (${ agent.getLastTS() })
      % elif agent.isRecording():
      As soon as the export process has finished, click
      <a href="#" onclick="javascript:activateAgent('${ agent.getId() }'); return false;">here</a>.
      % else:
      Agent not active. Start the <a href="#" onclick="javascript:preActivateAgent('${ agent.getId() }'); return false;">activation process</a>.
      % endif
      </td>
      <td>
        <a href="#" onclick="javascript: editAgent('${ agentId }'); return false;">Edit</a> <a href="#" onclick="javascript: deleteAgent('${ agentId }'); return false;">Delete</a>
      </td>
</tr>
% endfor
</table>

<a href="#" onclick="javascript:addAgent(); return false;">Add new agent</a>

<script type="text/javascript">

  var availableTypes = ${ jsonEncode(availableTypes) };
  var agentTableData = ${ jsonEncode(agentTableData) };
  var agentExtraOptions = ${ jsonEncode(extraAgentOptions) };

  function deleteAgent(agentId) {
      new ConfirmPopup($T('Agent activation'),
              $T("Are you sure you want to delete agent ") + agentId + "?",
              function(value) {
                  if (value) {
                     agentRequest('livesync.deleteAgent', agentId)
                  }
              }).open();
  }

  function addAgent() {
      var dialog = new AddAgentDialog(availableTypes, agentExtraOptions);
      dialog.open();
  }

  function preActivateAgent(agentId) {
      new ConfirmPopup($T('Agent activation'),
                       activateAgentText(agentId),
                       function(value) {
                           if (value) {
                              agentRequest('livesync.preActivateAgent', agentId)
                           }
                       }).open();
  }

  function activateAgent(agentId) {
      new ConfirmPopup(format($T("Activate '{0}'"), agentId),
          Html.div({style: {width: '350px'}},
                   $T('Are you sure you want to activate this agent? ' +
                      'Please make sure that the export process finished successfully')),
          function(value) {
              if (value) {
                  agentRequest('livesync.activateAgent', agentId);
              }
          }).open();
  }

  function editAgent(agentId) {
      var dialog = new EditAgentDialog(availableTypes,
                                       agentExtraOptions[agentTableData[agentId]._type],
                                       agentTableData[agentId]);
      dialog.open();
  }

</script>
