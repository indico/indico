<a name="Pic"></a>
<div class="groupItem">
    <div class="groupTitle"> ${ _("Picture Uploader")}</div>
    <div class="groupItemContent">
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
