<script type="text/javascript" src="%(baseURL)s/js/htmleditor/fckeditor.js"></script>
%(body)s
<script type="text/javascript">
<!--
var oFCKeditor = new FCKeditor( 'content' ) ;
oFCKeditor.Config["CustomConfigurationsPath"] = "%(baseURL)s/js/fckeditor/indicoconfig.js"  ;
oFCKeditor.Config["ImageUploadURL"] = "%(imageUploadURL)s" ;
oFCKeditor.Config["ImageBrowserURL"] = "%(imageBrowserURL)s";
oFCKeditor.Config["ImageBrowserWindowWidth"] = 700 ;
oFCKeditor.Config["ImageBrowserWindowHeight"] = 200 ;
oFCKeditor.Config["ImageDlgHideAdvanced"] = true ;
oFCKeditor.Config["ImageDlgHideLink"] = true ;
oFCKeditor.Config["LinkBrowser"] = false ;
oFCKeditor.BasePath       = "%(baseURL)s/js/fckeditor/" ;
oFCKeditor.Width          = 700 ;
oFCKeditor.Height         = 600 ;
oFCKeditor.ToolbarSet     = "IndicoPages" ;
oFCKeditor.ReplaceTextarea() ;
//-->
</script>
