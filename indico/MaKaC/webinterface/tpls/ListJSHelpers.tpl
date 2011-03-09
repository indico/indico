var newUser = false;

function selectStatuses()
{
    for (i = 0; i < document.filterOptionForm.statuses.length; i++)
    {
        document.filterOptionForm.statuses[i].checked=true;
    }
}

function selectOneStatus(elementName)
{
    var inputNodes = IndicoUtil.findFormFields($E(elementName))
    for (i = 0; i < inputNodes.length; i++)
    {
        var node = inputNodes[i];
        if (node.type == "checkbox") {
            node.checked = true;
        }
    }
}

function unselectOneStatus(elementName)
{
    var inputNodes = IndicoUtil.findFormFields($E(elementName))
    for (i = 0; i < inputNodes.length; i++)
    {
        var node = inputNodes[i];
        if (node.type == "checkbox") {
            node.checked = false;
        }
    }
}

function unselectStatuses()
{
    for (i = 0; i < document.filterOptionForm.statuses.length; i++)
    {
        document.filterOptionForm.statuses[i].checked=false
    }
}

var staticURLState = false;
var staticURLSwitch = function() {
    if (staticURLState) {
        IndicoUI.Effect.disappear($E('staticURL'));
        IndicoUI.Effect.disappear($E('staticURLLink'));
    } else {
        IndicoUI.Effect.appear($E('staticURL'));
        IndicoUI.Effect.appear($E('staticURLLink'));
        $E('staticURL').dom.select();
    }
    staticURLState = !staticURLState;
}

function isSelected(element) {
    var inputNodes = IndicoUtil.findFormFields($E(element))
    for (i = 0; i < inputNodes.length; i++) {
        var node = inputNodes[i];
        if (node.type == "checkbox") {
            if(node.checked == true) {
                $E(node.name+node.value).dom.style.backgroundColor = "#CDEB8B";
            } else {
                $E(node.name+node.value).dom.style.backgroundColor='transparent';
            }
        }
    }
}

function atLeastOneSelected(items, errorText) {
    if(!newUser) {
        var inputNodes = IndicoUtil.findFormFields(items)
        for (i = 0; i < inputNodes.length; i++)
        {
            var node = inputNodes[i];
            if (node.type == "checkbox") {
                if(node.checked == true) {
                    return true;
                }
            }
        }

        var dialog = new WarningPopup($T("Warning"), errorText);
        dialog.open();

        return false;
    } else {
        return true;
    }
}

function onMouseOver(element) {
    if ($E(element).dom.style.backgroundColor ==='transparent') {
       $E(element).dom.style.backgroundColor='rgb(255, 246, 223)';
    }
}

function onMouseOut(element) {
    var inputNodes = IndicoUtil.findFormFields($E(element))
    for (i = 0; i < inputNodes.length; i++) {
        var node = inputNodes[i];
        if (node.type == "checkbox") {
            if(node.checked !== true) {
                $E(node.name+node.value).dom.style.backgroundColor='transparent';
            } else {
                $E(node.name+node.value).dom.style.backgroundColor = "#CDEB8B";
            }
        }
    }
}

