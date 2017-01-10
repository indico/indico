/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
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

(function(global) {
    'use strict';

    $(document).ready(function() {
        setupSurveyScheduleWindows();
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
            var labels = $(elem).data('labels');
            var labelsHeight = labels.length * 20;
            var containerHeight = $(elem).parents('.i-box-content').outerHeight();
            new Chartist.Bar(elem, {
                labels: labels,
                series: [$(elem).data('series-absolute')]
            }, {
                horizontalBars: true,
                height: Math.max(labelsHeight, containerHeight) + 'px',
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

    global.setupQuestionnaireWindows = function setupQuestionnaireWindows() {
        $('.page-content').on('click', '.js-survey-item-dialog', function(evt) {
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
        }).on('indico:confirmed', '.js-delete-item', function(e) {
            e.preventDefault();

            var $this = $(this);
            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success: function(data) {
                    updateQuestions(data);
                    handleFlashes(data, true, $('#survey-questionnaire-preview'));
                }
            });
        });

        $('.js-add-question-dropdown').parent().dropdown({selector: '.js-add-question-dropdown'});
    };

    function setupSubmissionButtons() {
        $('#select-all').on('click', function() {
            $('#submission-list input:checkbox').prop('checked', true).trigger('change');
        });

        $('#select-none').on('click', function() {
            $('#submission-list input:checkbox').prop('checked', false).trigger('change');
        });

        $('.js-export-submissions').on('click', function() {
            var $this = $(this);

            var form = $('<form>', {
                method: 'POST',
                action: $this.data('href')
            });

            $('.submission-ids:checked').each(function() {
                $('<input>', {type: 'hidden', name: 'submission_ids', value: this.value}).appendTo(form);
            });

            form.appendTo('body').submit();
            form.remove();
        });

        function _disableButtons() {
            $('#delete-submissions').prop('disabled', !$('li.submission-row').length);
            $('.js-export-submissions').toggleClass('disabled', !$('li.submission-row').length);
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
        $('#survey-questionnaire-preview').sortable('destroy').html(data.questionnaire);
        $('.js-add-question-dropdown').parent().dropdown({selector: '.js-add-question-dropdown'});
        setupQuestionnaireSorter();
    }

    global.setupQuestionnaireSorter = function setupQuestionnaireSorter() {
        function _save(mode, data) {
            $.ajax({
                url: container.data('sort-url'),
                method: 'POST',
                data: $.extend({mode: mode}, data),
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError
            });
        }

        var container = $('#survey-questionnaire-preview');
        // sort sections
        container.sortable({
            items: '.js-sortable-survey-section',
            handle: '.ui-i-box-sortable-handle',
            placeholder: 'i-box-sortable-placeholder',
            tolerance: 'pointer',
            distance: 10,
            axis: 'y',
            start: function(e, ui){
                ui.placeholder.height(ui.helper.outerHeight());
            },
            update: function(e, ui) {
                var sectionIds = container.find('.js-sortable-survey-section').map(function() {
                    return $(this).data('sectionId');
                }).get();
                _save('sections', {
                    section_ids: sectionIds
                });
            }
        });
        container.find('.js-sortable-survey-items').sortable({
            items: '.survey-item',
            handle: '.ui-sortable-handle',
            connectWith: '#survey-questionnaire-preview .js-sortable-survey-items',
            tolerance: 'pointer',
            distance: 10,
            axis: 'y',
            start: function() {
                var $this = $(this);
                $this.css('min-height', $this.height());
            },
            stop: function() {
                $(this).css('min-height', '');
            },
            update: function(evt, ui) {
                var $this = $(this);
                // ignore update from the source list
                if (this !== ui.item.parent()[0]) {
                    return;
                }
                var itemIds = $this.find('.survey-item').map(function() {
                    return $(this).data('itemId');
                }).get();
                _save('items', {
                    item_ids: itemIds,
                    section_id: $this.closest('[data-section-id]').data('sectionId')
                });
            },
            receive: function() {
                $(this).removeClass('empty');
            },
            remove: function() {
                var $this = $(this);
                $this.toggleClass('empty', !$this.find('li:not(.empty-msg)').length);
            }
        });
    };
})(window);
