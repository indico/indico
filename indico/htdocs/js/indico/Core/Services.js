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

/**
     @namespace IndicoUI Services that are invisible
                in terms of user interface
    */

IndicoUI.Services = {
    /**
        * Asks the deletion of a subcontribution, reloading the page if
        * successful
        * @param {String} conference The conference id
        * @param {String} contribution The contribution id
        * @param {String} subContribution The subContribution id
        */
    deleteSubContribution : function(conference, contribution, subContribution) {
        jsonRpc(Indico.Urls.JsonRpcService, 'contribution.deleteSubContribution', {
            'conference': conference,
            'contribution': contribution,
            'subcontribution': subContribution
        }, function(response, error){
            var killProgress = IndicoUI.Dialogs.Util.progress();
            if (exists(error)) {
                killProgress();
                IndicoUtil.errorReport(error);
            }
            else {
                window.location.reload(true);
            }
        });
    },

    /**
        * Asks the deletion of a session, reloading the page if
        * successful
        * @param {String} conference The conference id
        * @param {String} session The session id
        */
    deleteSession : function(conference, session) {
        jsonRpc(Indico.Urls.JsonRpcService, 'schedule.event.deleteSession', {
            'conference': conference,
            'session': session
        }, function(response, error){
            var killProgress = IndicoUI.Dialogs.Util.progress();
            if (exists(error)) {
                killProgress();
                IndicoUtil.errorReport(error);
            }
            else {
                window.location.reload(true);
            }
        });
    }
};

