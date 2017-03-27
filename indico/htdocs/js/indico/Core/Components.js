/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
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

function imageFunctionGenerator(url) {
    return function (imageId, extension) {
        return url + '/' + imageId + '.' + (extension || 'png');
    };
}


var indicoSource = curry(jsonRpcValue, Indico.Urls.JsonRpcService);
var indicoRequest = curry(jsonRpc, Indico.Urls.JsonRpcService);
var imageSrc = imageFunctionGenerator(Indico.Urls.ImagesBase);


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
    loadTimeFuncs : {},

    executeOnLoad : function(func) {
        IndicoUI.loadTimeFuncs[IndicoUI.__loadCount] = (func);
        IndicoUI.__loadCount++;
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
