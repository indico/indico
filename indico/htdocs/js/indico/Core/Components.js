/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */


if(!window.indicoOfflineSite) {
    include(ScriptRoot + "ckeditor/ckeditor.js");
}

var indicoSource = null;
var indicoRequest = null;
var imageSrc = null;

function imageFunctionGenerator(url) {
    return function (imageId) {
        if (Indico.SystemIcons[imageId]) {
            return url + '/' + Indico.SystemIcons[imageId];
        } else {
            return url + '/' + imageId;
        }
    };
}

if (location.protocol == "https:") {
    function fixUrls(urls) {
        for(var key in urls) {
            // flask router -> skip
            if(urls[key].type == 'flask_rules') {
                continue;
            }

            // not a string -> assume object and recurse
            if(urls[key].replace === undefined) {
                fixUrls(urls[key]);
                continue;
            }

            // skip if the url starts with https or it's ImagesBase
            if(urls[key].indexOf('https:') === 0) {
                continue;
            }

            if(urls['Secure' + key]) {
                // we alraedy have a secure url, e.g. for ImageBase
                urls[key] = urls['Secure' + key];
            }
            else {
                urls[key] = urls[key].replace(/^http:/, 'https:');
            }
        }
    }

    fixUrls(Indico.Urls);
}

indicoSource = curry(jsonRpcValue, Indico.Urls.JsonRpcService);
indicoRequest = curry(jsonRpc, Indico.Urls.JsonRpcService);
imageSrc = imageFunctionGenerator(Indico.Urls.ImagesBase);


function getPx(pixVal) {
    var m = pixVal.match(/(\d+)px/);
    return parseInt(m[1], 10);
}


function pixels(val){
    return val + 'px';
}

function zeropad(number) {
    return ((''+number).length == 1)?'0'+number:number;
}


/**
 @namespace IndicoUI interface library
*/

var IndicoUI = {
    // The current used layer level
    __globalLayerLevel : 0,

    // To keep track of all used layer levels.
    // A used level is set to true and level 0 is always used
    __globalLayerLevels : [true],

    /**
     * Set the element's z-index to the top layer
     */
    assignLayerLevel: function(element) {
        if (!exists(element))
            return;
        // Find the highest used layer
        for (var i = this.__globalLayerLevel; i >= 0; i--) {
            if (this.__globalLayerLevels[i]) {
                this.__globalLayerLevel = i;
                break;
            }
        }

        var level = ++this.__globalLayerLevel;
        this.__globalLayerLevels[level] = true;
        element.setStyle('zIndex', this.__globalLayerLevel + 3000);
    },
    /**
     * Marks a layer level as unused, call this funtion
     * when closing an element
     */
    unAssignLayerLevel: function(element) {
        if (!exists(element))
            return;
        var level = element.dom.style.zIndex;
        if (level == '') {
            return;
        }
        this.__globalLayerLevels[parseInt(level) - 3000] = false;
    },
    __loadCount : 0,
    __unloadCount : 0,
    loadTimeFuncs : {},
    unloadTimeFuncs : {},

    executeOnLoad : function(func) {
        IndicoUI.loadTimeFuncs[IndicoUI.__loadCount] = (func);
        IndicoUI.__loadCount++;
    },

    executeOnUnload : function(func) {
        IndicoUI.unloadTimeFuncs[IndicoUI.__unloadCount] = (func);
        IndicoUI.__unloadCount++;
    }

};

$(function() {
    for (var f in IndicoUI.loadTimeFuncs) {
        IndicoUI.loadTimeFuncs[f]();
    }

    $E(document.body).observeClick(function(e) {
        each(IndicoUtil.onclickFunctions, function(func) {
            if (exists(func)) {
                func(e);
            }
        });

        //two-phase delete, due to loop/delete interactions
        var idxs = [];
        var count = 0;

        each(IndicoUtil.onclickFunctions, function(func) {
            if (func === null) {
                idxs.push(count);
            }
            count++;
        });

        idxs.reverse();

        each(idxs, function(idx) {
            IndicoUtil.onclickFunctions.removeAt(idx);
        });
    });
});

window.onunload = function() {
    for (var f in IndicoUI.unloadTimeFuncs) {
        IndicoUI.unloadTimeFuncs[f]();
    }
};
