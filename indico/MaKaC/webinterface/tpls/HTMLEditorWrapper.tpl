<script type="text/javascript" src="%(baseURL)s/js/ckeditor/ckeditor.js"></script>
%(body)s
<script type="text/javascript">

    var editor = new ParsedRichTextWidget(500, 200,"", "rich", "IndicoFull");
    editor.set($E('content').dom.value);
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
