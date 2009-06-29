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

