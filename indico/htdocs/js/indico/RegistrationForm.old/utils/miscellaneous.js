/* This file is part of Indico.
 * Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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


// If index of is not implemented (e.g Internet explorer 8)
if(!Array.indexOf){
  Array.prototype.indexOf = function(obj){
    for(var i=0; i<this.length; i++){
        if(this[i]==obj){
            return i;
        }
    }
    return -1;
  };
}

var getConfId = function (){
    return $("#conf_id").val();
    var url = location.search.substring(1);
    var params = url.split("&");
    var val;
    var paramsArray = [];
    for ( var i=0; i<params.length;i++) {
        val = params[i].split("=");
        paramsArray[val[0]]=val[1];
    }
    return paramsArray.confId;
};

// convert an array [ { name:thename, value: thevalue} , ... ] to
// { thename : thevalue }
var toDict = function ( array ){
    var dict = {};
    $.each(array, function ( ind, el ) {
        dict[el.name] = el.value;
    });
    return dict;
};

/*
 * Simple temporary element manager
 */
var ElementManager = Backbone.Model.extend({
    defaults : {
        tmpClass: "tmpElements",
        hiddenClass: "hiddenElements"
    },
    initalize : function(){},
    addHidden : function ( el ) {
        $(el).hide();
        return $(el).addClass(this.get("hiddenClass"));
    },
    addTmp : function ( el ) {
        return $(el).addClass(this.get("tmpClass"));
    },
    showHidden : function() {
        $("."+this.get("hiddenClass")).show();
    },
    removeTmp : function () {
        $("."+this.get("tmpClass")).remove();
    }
});

var nunenv = new nunjucks.Environment(new nunjucks.HttpLoader('/indico/js/indico/RegistrationForm/templates'));
nunenv.addExtension('i18nExtension', new i18nExtension());
