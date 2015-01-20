
<table width="100%">
    <tr>
        <form action=${ saveLinkURL } method="POST" onsubmit="return parseForm(this)">
        <td bgcolor="white" width="90%" valign="top" style="padding-left:20px">
                <table width="60%" align="left" valign="middle" style="padding-top:20px" border="0">
                    <tr>
                        <td colspan="2" class="subgroupTitle"> ${ _("Create internal web page")}</td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Name")}</span></td>
                        <td bgcolor="white" width="100%"><input type="text" name="name" size="50"></td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Content")}</span></td>
                        <td>
                            <div id="contentField"></div>
                            <input type="hidden"  id="content" name="content">
                        </td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Display target")}</span></td>
                        <td bgcolor="white" width="100%">
                          <input type="radio" name="displayTarget" value="" CHECKED> ${ _("Display in the SAME window")}<br>
                          <input type="radio" name="displayTarget" value="_blank"> ${ _("Display in a NEW window")}
                        </td>
                    </tr>
                    <tr>
                        <td bgcolor="white" colspan="2" align="center" width="100%">
                            <input type="submit" class="btn" name="submit" value="${ _("save")}">
                            <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
                        </td>
                    </tr>
                </table>
            </form>
        </td>
    </tr>
</table>
<br>
<script type="text/javascript">
    var editor = new ParsedRichTextWidget(600, 400, "", "rich");
    editor.set("${ content }", true);
    $E('contentField').set(editor.draw());

    function parseForm(form){
        with(form){
            if(editor.clean()){
                $E('content').set(editor.get());
                return true;
            } else
                return false;
        }
    }
</script>
