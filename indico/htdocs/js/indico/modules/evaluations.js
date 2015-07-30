(function(global) {
    'use strict';

    $(document).ready(function() {
        setupQuestionWindows();
    });

    global.setupQuestionWindows = function setupQuestionWindows() {
        $('a.js-question-dialog').on('click', function(evt) {
            evt.preventDefault();
            ajaxDialog({
                url: build_url($(this).data('href')),
                title: $(this).data('title'),
                onClose: function(data) {
                    if (data) {
                        location.reload();
                    }
                }
            });
        });
    };
})(window);
