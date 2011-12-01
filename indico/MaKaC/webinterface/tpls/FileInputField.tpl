<div id="newAttachment${htmlName}"></div>
<div id="existingAttachment${htmlName}"></div>
<td></td>
<td align="right" valign="bottom"></td>
</tr>
% if field._parent.getDescription():
<tr><td colspan="2">${field._getDescriptionHTML(field._parent.getDescription())}</td>
% endif

<script type="text/javascript">

var imageRemove = Html.img({
    src: imageSrc("remove"),
    alt: $T('Remove attachment'),
    title: $T('Remove this attachment'),
    id: 'removeAttachment',
    style:{marginLeft:'15px', cursor:'pointer', verticalAlign:'bottom'}
});

var uploadFileInput = Html.input('file', {id: '${htmlName}', name: '${htmlName}'});
var existingAttachment = Html.div({}, $('${field.getValueDisplay(value) if value else ""}')[0],
                                      imageRemove,
                                      Html.input("hidden",{id: '${htmlName}', name: '${htmlName}'}, '${value.getFileName() if value else ""}'));

$(imageRemove.dom).click(function(e) {
    $E("newAttachment${htmlName}").set(uploadFileInput);
});

% if value:
    $E("newAttachment${htmlName}").set(existingAttachment);
% else:
    $E("newAttachment${htmlName}").set(uploadFileInput);
% endif

% if field._parent.isMandatory():
    addParam($E('${htmlName}'), 'text', false);
% endif

</script>

