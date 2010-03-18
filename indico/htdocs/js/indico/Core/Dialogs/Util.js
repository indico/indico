IndicoUI.Dialogs.Util = {

    error: function(err) {
        var dialog = null;
        if (exists(err.type) && err.type === "noReport") {
            dialog = new NoReportErrorDialog(err);
        } else {
            dialog = new ErrorReportDialog(err);
        }
        dialog.open();
    },

    progress: function(text) {
        var dialog = new ProgressDialog(text);
        dialog.open();

        return function() {
            dialog.close();
        };
    },

    alert: function(title, message) {
        var popup = new AlertPopup(title, message);
        popup.open();
    },

    confirm: function(title, message, handler) {
        var popup = new ConfirmPopup(title, message, handler);
        popup.open();
    }
};
