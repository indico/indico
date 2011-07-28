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

    blockMoveProgress: function(text) {
      var message = (text != undefined) ? $T(text) : "";
      var loadingImage = $('<div class= "blockMoveProgressImage"></div>');
      var loadingText = $('<div class="blockMoveProgressText"></div>').html(message);
      var progress = $('<div class="blockMoveProgress"></div>').append(loadingImage, loadingText);

      $('body').append(progress);
        return function() {
          $(progress).remove();
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
