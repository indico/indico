<script type="text/javascript" src="${ baseURL }/js/htmleditor/fckeditor.js"></script>
<form action="${ postURL }" method="POST">
    <br>
    <table width="50%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle">
                 ${ _("Write your minutes")}
                [<a href="#" onClick="setHTML();this.disabled=true;return false;"><font class="groupLink"> ${ _("use html editor")}</font></a>]
            </td>
        </tr>
        <tr>
            <td bgcolor="white" width="100%" colspan="3" bgcolor="#EAEAEA">
                <textarea cols="100" rows="20" name="text">${ text }</textarea>
            </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td align="left">
                <input type="submit" class="btn"  name="OK" value="${ _("save")}">
                <input type="submit" class="btn"  name="cancel" value="${ _("cancel")}">
                &nbsp;&nbsp;&nbsp;&nbsp;
                ${ compileButton }
                <input type="button" class="btn"  name="clear" value="${ _("clear")}" onClick="this.form.text.value='';">
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
    oFCKeditor.Config["CustomConfigurationsPath"] = "${ baseURL }/js/htmleditor/indicoconfig.js"  ;
    oFCKeditor.Config["ImageUploadURL"] = "${ imageUploadURL }" ;
    oFCKeditor.Config["ImageBrowserURL"] = "${ imageBrowserURL }";
    oFCKeditor.Config["ImageBrowserWindowWidth"] = 700 ;
    oFCKeditor.Config["ImageBrowserWindowHeight"] = 200 ;
    oFCKeditor.Config["ImageDlgHideAdvanced"] = true ;
    oFCKeditor.Config["ImageDlgHideLink"] = true ;
    oFCKeditor.Config["LinkBrowser"] = false ;
    oFCKeditor.BasePath       = "${ baseURL }/js/htmleditor/" ;
    oFCKeditor.Width          = 650 ;
    oFCKeditor.Height         = 500 ;
    oFCKeditor.ToolbarSet     = "Indico" ;
    oFCKeditor.ReplaceTextarea() ;
  }
}
//-->
</script>