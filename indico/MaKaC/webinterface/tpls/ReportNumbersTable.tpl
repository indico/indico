<table>
	<tr>
        <td>
            <form action=%(addURL)s method="POST">
                <table>
                    <tr>
                        <td>
                        </td>
                        <td>
                            <select name="reportNumberSystem">
                                <option value="notype" selected> --  select a system -- </option>
                                %(repTypesSelectItems)s
                            </select>
                        </td>
                        <td>
                            <input type="submit" class="btn" value="add">
                        </td>
                    </tr>
                </table>
            </form>
        </td>
    </tr>
	
    <tr>
        <td class="blacktext">
            <form action=%(deleteURL)s method="POST">
                <ul style="display:block; list-style-type: none; padding-left: 0px;">                    
					<% for (id, number, name) in items: %>
					<li style="margin: 0; display: block; height: 20px;">
						<span style="float:left">
							<strong><%= name %> :</strong>  <%= number %>
						</span>
						<input 	type="image" class="UIRowButton"
							onclick="javascript:removeRptItem('<%= id %>', this.form);return false;"
							title="<%= _("Remove this report number from the list")%>"
							src="<%= systemIcon("remove") %>" />
					</li>
					<% end %>
                </ul>
				<div>
					<input type="hidden" id="removeParams" name="deleteReportNumber" value="" >
				</div>            	
			</form>
        </td>
	</tr>

</table>

<script type="text/javascript">
	
function removeRptItem(value, form) {	
	$E('removeParams').dom.value=value;
	form.submit();
};

</script>
