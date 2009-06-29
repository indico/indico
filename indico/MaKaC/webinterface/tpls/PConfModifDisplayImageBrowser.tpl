<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<link href="%(baseURL)s/htmleditor/editor/skins/default/fck_dialog.css" rel="stylesheet" type="text/css" />
<script>
function OpenFile( fileUrl )
{
	window.top.opener.SetUrl( fileUrl ) ;
	window.top.close() ;
	window.top.opener.focus() ;
}
</script>
</head>
<body scroll="no" style="overflow: hidden">
<table height="100%%" cellspacing="0" cellpadding="0" width="100%%" border="0">
<tr>
  <td id="TitleArea" class="PopupTitle PopupTitleBorder">
     <%= _("Image Browser")%>
  </td>
</tr>
<tr>
  <td id="FrameCell" height="100%%" valign="top">
    %(body)s
  </td>
</tr>
<tr>
  <td class="PopupButtons">
    <table border="0" cellpadding="0" cellspacing="0">
    <tr>
      <td width="100%%">&nbsp;</td>
      <td nowrap="nowrap">
        <input type="button" value="<%= _("Close")%>" class="Button" onclick="window.close();" />
      </td>
    </tr>
    </table>
  </td>
</tr>
</table>
</body>
</html>