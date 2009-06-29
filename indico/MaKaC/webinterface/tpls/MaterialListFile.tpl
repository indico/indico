<li>
	<a href=%(fileAccessURL)s>%(fileName)s</a> 
	%(fileInfo)s 
	<input type="image" name="%(delName)s" src="%(deleteIconURL)s" alt="delete the file" onclick="return confirm('<%= _("Are you sure you want to delete this file?")%>');" style="vertical-align:middle;" />
		%(fileActions)s
</li>
