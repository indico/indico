(function(global) {
    'use strict';

    $(document).ready(function() {
        setupSurveyScheduleWindows();
        setupQuestionWindows();
        setupSurveyResultCharts();
        setupSubmissionButtons();
    });

    function setupSurveyResultCharts() {
        $('#survey-results .survey-pie-chart').each(function(idx, elem) {
            var chart = new Chartist.Pie(elem, {
                labels: $(elem).data('labels'),
                series: $(elem).data('series-relative')
            }, {
                donut: true,
                donutWidth: 20,
                startAngle: 270,
                total: 1,
                chartPadding: 20,
                labelOffset: 20,
                labelDirection: 'explode'
            }).on('draw', function removeEmptyLabels(data) {
                if (data.value === 0) {
                    chart.data.labels[data.index] = '';
                }
            });
        });

        $('#survey-results .survey-bar-chart').each(function(idx, elem) {
            new Chartist.Bar(elem, {
                labels: $(elem).data('labels'),
                series: [$(elem).data('series-absolute')]
            }, {
                horizontalBars: true,
                reverseData: true,
                axisX: {
                    onlyInteger: true,
                },
                axisY: {
                    offset: 50
                }
            });
        });
    }

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
                    handleFlashes(data, true, $('#questionnaire-preview'));
                }
            });
        });

        $('.js-add-question-dropdown').parent().dropdown({selector: '.js-add-question-dropdown'});
    }

    function setupSubmissionButtons() {
        $('#select-all').on('click', function() {
            $('#submission-list input:checkbox').prop('checked', true).trigger('change');
        });

        $('#select-none').on('click', function() {
            $('#submission-list input:checkbox').prop('checked', false).trigger('change');
        });

        $('#export-submissions').on('click', function(evt) {
            var $this = $(this);

            var form = $('<form>', {
                method: 'POST',
                action: $this.data('href'),
            });

            $('.submission-ids:checked').each(function() {
                $('<input>', {type: 'hidden', name: 'submission_ids', value: this.value}).appendTo(form);
            });

            form.appendTo('body').submit();
            form.remove();
        });

        function _disableButtons() {
            $('#export-submissions, #delete-submissions').prop('disabled', !$('li.submission-row').length);
            $('#delete-submissions').prop('disabled', !$('.submission-ids:checked').length);
        }

        $('.js-delete-submission').on('indico:confirmed', function(evt) {
            evt.preventDefault();
            var $this = $(this);

            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                data: {
                    submission_ids: $this.data('submission-id')
                },
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success: function() {
                    $this.closest('.submission-row').remove();
                    _disableButtons();
                }
            });

        });

        $('#delete-submissions').on('indico:confirmed', function(evt) {
            evt.preventDefault();
            var $this = $(this);
            var submissionIds = $('.submission-ids:checked').map(function() {
                return $(this).val();
            }).get();

            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                data: {
                    submission_ids: submissionIds
                },
                traditional: true,
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success: function() {
                    $('.submission-ids:checked').closest('.submission-row').remove();
                    _disableButtons();
                }
            });
        });

        $('.submission-ids').change(function() {
            $('#delete-submissions').prop('disabled', !$('.submission-ids:checked').length);
        });
    }

    function updateQuestions(data) {
        $('#questionnaire-preview').tablesorter('destroy').html(data.questionnaire);
        setupQuestionSorter();
    }

    global.setupQuestionSorter = function setupQuestionSorter() {
        var container = $('#questionnaire-preview');
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
