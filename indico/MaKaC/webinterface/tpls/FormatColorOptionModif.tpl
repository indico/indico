<form id="${ formatOption }Form" action="${changeColorURL}" method="post">
    <div class="colorField"></div>
    <input type="submit" name="apply" value="${ _("Apply color")}">
    <input type="submit" name="remove" value="${ _("Remove color")}" style="display: ${ 'none' if  colorCode == '' else 'inline'};">
</form>

<script type="text/javascript">
    $("#${formatOption}Form > div.colorField").html(new ColorPickerWidget("colorCode", ${colorCode.replace("#","") | n, j}).draw());
</script>
