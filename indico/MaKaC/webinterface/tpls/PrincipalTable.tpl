<form action="<%= removePrincipalsURL %>" method="post">
<%= locator %>
<ul class="UIPeopleList">
    <%= userItems %>
</ul>
<div style="margin-top: 20px;">
	<input type="hidden" name="selectedPrincipals" value="" >
	<input type="submit" class="btn" value="<%= _("Add user to list")%>" onClick="this.form.action='<%= addPrincipalsURL %>';" >
</div>
</form>

<script type="text/javascript">
	function removeItem(number, form)
	{
		form.selectedPrincipals.value = number;
		form.submit();
	}
</script>