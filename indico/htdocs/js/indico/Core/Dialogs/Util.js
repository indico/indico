IndicoUI.Dialogs.Util = {
    error: function(err) {
        var dialog = new ErrorReportDialog(err);
        dialog.open();
    },

    progress: function(text) {
        var dialog = new ProgressDialog(text);
        dialog.open();

        return function() {
            dialog.close();
        };
    }
};