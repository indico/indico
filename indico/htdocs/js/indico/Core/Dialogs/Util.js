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

    ttStatusInfo: function(text) {
        var stext = $('<div class="text"></div>').text(text ? $T(text) : null);
        var image = $('<img/>', {
            src: "images/loading.gif",
            alt: $T('Loading...')
        });

        var progress = $('<div id="tt_status_info" class="tt_tmp_button"></div>').
            append(image, stext);

        $('#tt_status_info').replaceWith(progress).show();
        progress.fadeIn();

        return function() {
            progress.hide();
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
