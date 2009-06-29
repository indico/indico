<script type="text/javascript" src="%(baseURL)s/js/htmleditor/fckeditor.js"></script>
<form action="%(postURL)s" method="POST">
    <br>
    <table width="50%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle">
                 <%= _("Write your minutes")%>
                [<a href="#" onClick="setHTML();this.disabled=true;return false;"><font class="groupLink"> <%= _("use html editor")%></font></a>]
            </td>
        </tr>
        <tr>
            <td bgcolor="white" width="100%%" colspan="3" bgcolor="#EAEAEA">
                <textarea cols="100" rows="20" name="text">%(text)s</textarea>
            </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td align="left">
                <input type="submit" class="btn"  name="OK" value="<%= _("save")%>">
                <input type="submit" class="btn"  name="cancel" value="<%= _("cancel")%>">
                &nbsp;&nbsp;&nbsp;&nbsp;
                %(compileButton)s
                <input type="button" class="btn"  name="clear" value="<%= _("clear")%>" onClick="this.form.text.value='';">
            </td>
        </tr>
    </table>
</form>

<script type="text/javascript">
<!--
var oFCKeditor = "";

function setHTML() {
  if (oFCKeditor == "") {
    oFCKeditor = new FCKeditor( 'text' ) ;
    oFCKeditor.Config["CustomConfigurationsPath"] = "%(baseURL)s/js/htmleditor/indicoconfig.js"  ;
    oFCKeditor.Config["ImageUploadURL"] = "%(imageUploadURL)s" ;
    oFCKeditor.Config["ImageBrowserURL"] = "%(imageBrowserURL)s";
    oFCKeditor.Config["ImageBrowserWindowWidth"] = 700 ;
    oFCKeditor.Config["ImageBrowserWindowHeight"] = 200 ;
    oFCKeditor.Config["ImageDlgHideAdvanced"] = true ;
    oFCKeditor.Config["ImageDlgHideLink"] = true ;
    oFCKeditor.Config["LinkBrowser"] = false ;
    oFCKeditor.BasePath       = "%(baseURL)s/js/htmleditor/" ;
    oFCKeditor.Width          = 650 ;
    oFCKeditor.Height         = 500 ;
    oFCKeditor.ToolbarSet     = "Indico" ;
    oFCKeditor.ReplaceTextarea() ;
  }
}
//-->
</script>