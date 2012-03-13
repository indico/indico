<a name="Pic"></a>
<div class="groupItem">
    <div class="groupTitle"> ${ _("Picture Uploader")}</div>
    <em>${_("This page allows you to upload pictures which you can later link to from any Indico page (e.g. Event Home Page). Indico will generate a URL for each picture.")}</em>
    <div class="groupItemContent" style="padding-top:5px;">
        <div id="picsToolBar" class="picsToolBar"></div>
        <div id="picsContainer" class="picsContainer"></div>
    </div>
</div>

<script type="text/javascript">
<!--
    var picsList = new PicList(${ jsonEncode(picsList) }, 'picsContainer', '${ urlHandlers.UHSavePic.getURL( self_._conf ) }', '${ self_._conf.getId() }');
    var addButton = Widget.link(command(function(){
                                            picsList.addItem();
    },IndicoUI.Buttons.addButton()));
    $E("picsToolBar").set(addButton);
-->
</script>
