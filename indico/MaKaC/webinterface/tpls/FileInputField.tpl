<td><div id="attachment${htmlName}" class="existingAttachment"></div></td>
<td align="right" valign="bottom"></td>
</tr>
% if field._parent.getDescription():
<tr><td colspan="2">${field._getDescriptionHTML(field._parent.getDescription())}</td>
% endif

<script type="text/javascript">

$E("attachment${htmlName}").set(new RegistrationUploadFile(${htmlName | n,j},
        ${field.getValueDisplay(value) if value else "" | n,j},
        ${value.getFileName() if value else "" | n,j},
        ${field.getParent().isMandatory() | n,j}).draw());

if(${field.getParent().isMandatory() | n,j}){
    addParam($E('${htmlName}'), 'text', false);
}

</script>

