<li class="UIGroup">
<span class="nameLink">
% if selectable: 
<input type="${ type }" name="selectedPrincipals" value="${ id }" ${ selected }>
% endif
${ fullName }</span>

% if not selectable: 
<input     type="image" class="UIRowButton"
            onclick="javascript:removeItem('${ id }', this.form);return false;"
            title="${ _("Remove this person from the list")}"
            src="${ systemIcon("remove") }" />
% endif
</li>