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


var TemplateManager = {

    templates: {},

    loadCache: function(context, fileNameList){
        var self = this;
        var counter = fileNameList.length;
        var defer = $.Deferred();
        _.each(fileNameList, function(fileName){
            var template = self.templates[context + fileName];
            if (typeof template == 'undefined'){
                $.ajax({
                    type: 'GET',
                        url: ScriptRoot + '/indico/' + context + '/templates/' + fileName + '.tpl',
                        dataType: "html",
                        async: true,
                        success: function(tpl){
                            counter = counter - 1;
                            self.templates[context + fileName] = tpl;
                            if(counter == 0){
                                defer.resolve();
                            }
                        }
                    });
            }
        });
        return defer;
    },

    getCached: function(context, fileName, tplId){
        var template = this.templates[context + fileName];
        if( tplId !== false ) {
            template = $(template).siblings('#'+tplId).html();
        }
        return template;
    },


    get: function(context, fileName, tplId, callback) {
        var self = this;
        var template = this.templates[context + fileName];
        if (template){
            if( tplId !== false ) {
                template = $(template).siblings('#'+tplId).html();
            }
            callback(templates);
        } else {
            $.ajax({
                type: 'GET',
                    url: ScriptRoot + '/indico/' + context + '/templates/' + fileName + '.tpl',
                    dataType: "html",
                    async: true,
                    success: function(template){
                        self.templates[context + fileName] = template;
                        if( tplId !== false ) {
                            template = $(template).siblings('#'+tplId).html();
                        }
                        callback(template);
                    }
                });
        }
        return false;
    },

    getSync: function (context, fileName, tplId) {
        var self = this;
        var template = this.templates[context + fileName];
        if (typeof template == 'undefined'){
            var self = this;
            $.ajax({
                type: 'GET',
                    url: ScriptRoot + '/indico/' + context + '/templates/' + fileName + '.tpl',
                    dataType: "html",
                    async: false,
                    success: function(tpl){
                        self.templates[context + fileName] = tpl;
                        template = tpl;
                    }
                });
        }
        if( tplId !== false ) {
            template = $(template).siblings('#'+tplId).html();
        }
        return template;
    }
};