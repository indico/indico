<h2 class="formTitle"><%= _("User Preferences")%></h2>
<h3>Site-wide</h3>
<table style="margin-left: 100px;">
	<tr>
	    <td class="titleCellTD"><span class="titleCellFormat"><%= _("Modification Tabs")%></span></td>
	    <td class="blacktext spaceLeft" id="tabExpandSelect"></td>
	</tr>
</table>


<script type="text/javascript">

	var source = jsonRpcObject(Indico.Urls.JsonRpcService, "user.personalinfo.set", {value: null});

	source.state.observe(function(state) {
           // wait for the source to be loaded
	   if (state == SourceState.Loaded) {
        	IndicoUI.Widgets.Generic.sourceSelectionField($E('tabExpandSelect'), 
	   					  $C(source.accessor('tabAdvancedMode'), {
		                                     toTarget: function(value) {
			                                  return str(value);
			                             },
			                             toSource: function(value) {
			                                  return value == "true";
			                             }
			                          }),
				                 {'false': 'Basic',
					          'true': 'Advanced'});             
	   }
	});
	


</script>
