<table width="100%">
  <tr>
    <td width="100%">
      <form action=<%= removeSpeakersURL %> method="POST">
        <%= authors %>
    </td>
  </tr>
  <tr>
	<td valign="bottom" align="right">
		<table valign="bottom">
		<tr>
		    <td valign="bottom">
         	   	<input type="submit" class="btn" name="REMOVE" value="<%= _("remove")%>" style="width:80px">
		    </td>
            </form>
		</tr>
		<tr>
			<form action=<%= newSpeakerURL %> method="POST">
			<td valign="bottom">
			<input type="submit" class="btn" name="new" value="<%= _("new")%>" style="width:80px">
			</td>
			</form>
	  	</tr>
	  	<tr>
			<form action=<%= searchSpeakersURL %> method="POST">
			<td valign="bottom">
			<input type="submit" class="btn" name="search" value="<%= _("search")%>" style="width:80px">
			</td>
			</form>
	  	</tr>

		</table>
	</td>
  </tr>
</table>