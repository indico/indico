var WR_contributionsLoaded = false;

var WR_hideTalks = function (){
    IndicoUI.Effect.disappear($E('contributionsDiv'));
}

var WR_loadTalks = function () {
    IndicoUI.Effect.appear($E('contributionsDiv'));
}

var setDisabled = function (div)
{

    var nodesToDisable = {button :'', input :'', optgroup :'',
                        option :'', select :'', textarea :''};

    var node, nodes;
    nodes = div.getElementsByTagName('*');
    if (!nodes) return;

    var i = nodes.length;
    while (i--){
        node = nodes[i];
        if ( node.nodeName && node.nodeName.toLowerCase() in nodesToDisable ){
            node.disabled = true;
        }
    }
}
