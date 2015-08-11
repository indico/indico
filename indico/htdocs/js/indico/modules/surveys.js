(function(global) {
    'use strict';

    $(document).ready(function() {
        setupSurveyScheduleWindows();
        setupQuestionWindows();
    });

    function setupSurveyScheduleWindows() {
        $('a.js-survey-schedule-dialog').on('click', function(evt) {
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
    }

    function setupQuestionWindows() {
        $('.page-content').on('click', '.js-question-dialog', function(evt) {
            evt.preventDefault();
            ajaxDialog({
                trigger: this,
                url: $(this).data('href'),
                title: $(this).data('title'),
                onClose: function(data) {
                    if (data) {
                        updateQuestions(data);
                    }
                }
            });
        }).on('indico:confirmed', '.js-delete-question', function(e) {
            e.preventDefault();

            var $this = $(this);
            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success: function(data) {
                    updateQuestions(data);
                    handleFlashes(data, true, $('#questions'));
                }
            });
        });
    }

    function updateQuestions(data) {
        $('#questions').tablesorter('destroy').html(data.questionnaire);
        setupQuestionSorter();
    }

    global.setupQuestionSorter = function setupQuestionSorter() {
        var container = $('#questions');
        container.tablesorter({
            sortables: '.sortblock ul',
            sortableElements: '> li',
            placeholderElement: '<li></li>',
            handle: '.question-data',
            onReorder: function() {
                var questionIds = $('[data-question-id]').map(function() {
                    return $(this).data('question-id');
                }).get();

                $('.position-element').each(function(index, obj) {
                    $(obj).text((index + 1) + '.');
                });

                $.ajax({
                    url: container.data('sort-url'),
                    method: 'POST',
                    data: {
                        question_ids: questionIds
                    },
                    traditional: true,
                    complete: IndicoUI.Dialogs.Util.progress(),
                    error: handleAjaxError
                });
            }
        });
    };
})(window);
