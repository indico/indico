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

var RegFormBaseModel = Backbone.Model.extend({

    url: Indico.Urls.JsonRpcService,

    setResult: function(result){
        this.set(result);
    },

    parse: function(resp, xhr){
        if (exists(resp.error)) {
            IndicoUtil.errorReport(resp.error);
        } else if (exists(resp.result.hasWarning) && resp.result.hasWarning === true) {
            var popup = new WarningPopup(resp.result.warning.title, resp.result.warning.content);
            popup.open();
            this.setResult(resp.result.result);
        } else {
            this.setResult(resp.result);
        }
    },

    //Has to be overwritten
    fetchMethod: '',

    fetch: function(){
        var options = {};
        options.type = 'POST';
        options.contentType = 'application/json; charset=utf-8';
        options.dataType = 'json';
        options.headers = {};
        var token = $('#csrf-token').attr('content');
        if (token) {
                options.headers["X-CSRF-Token"] =  token;
        }
        var data = {
                version: '1.1',
                origin: document.URL,
                method: this.fetchMethod
        };
        data.params = {confId: getConfId()};
        options.data = JSON.stringify(data);
        return Backbone.Model.prototype.fetch.call(this, options);
    },

    commitDefaultParams: function(params){
        params.confId = getConfId();
        return params;
    },

    setHighlights: function(hl){
        this.highlights = hl;
    },

    getHighlights: function(){
        return any(this.highlights,[]);
    },

    addHighlights: function(hl){
        this.highlights = any(this.highlights,[]);
        this.highlights.push(hl);
    },

    emptyHighlights: function(hl){
        this.highlights = [];
    },

    _commit: function(method, params, updateModel, updateSilent) {
        var self = this;
        params = this.commitDefaultParams(params);
        indicoRequest('regForm.registrationForm.' + method, params,
                function(result, error){
                    if (exists(error)) {
                        IndicoUtil.errorReport(error);
                    } else {
                        if (exists(result.hasWarning) && result.hasWarning === true) {
                            var popup = new WarningPopup(result.warning.title, result.warning.content);
                            popup.open();
                            result = result.result;
                            self.trigger('change');
                        } else if (exists(result.highlight)) {
                            self.addHighlights(result.highlight);
                            result = result.result;
                        }

                        if(updateModel === true){
                            self.set( result, { silent: updateSilent } );
                        } else if (_.isFunction(updateModel)){
                            updateModel(result, updateSilent);
                        }
                    }
                });
        return false;
    }
});