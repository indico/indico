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

(function($) {
    'use strict';

    $.widget('indico.timerange', {
        options: {
            label: $T('Time'),
            initStartTime: '0:00',
            initEndTime: '23:59',
            startTimeName: 'start_time',
            endTimeName: 'end_time',
            wrapInToolbar: true,
            thinToolbar: true,
            errorHighlight: true,
            sliderWidth: '230px',
            change: null
        },

        _create: function() {
            var self = this;
            var element = self.element;
            var opt = self.options;

            var toolbar = element;
            var group = $('<div class="group with-slider timerange">');
            var label = $('<span class="i-button label heavy">').text(opt.label);
            var range = $('<span class="i-button label slider">').css('width', opt.sliderWidth);
            var thinClass = opt.thinToolbar ? 'thin' : '';

            self._createInputs();
            self._createSlider();

            if (opt.wrapInToolbar) {
                toolbar = $('<div class="toolbar {0}">'.format(thinClass));
                element.append(toolbar);
            }

            group.append(label)
                .append(self.startTime)
                .append(range
                    .append(self.slider))
                .append(self.endTime)
                .appendTo(toolbar);
        },

        _createInputs: function() {
            var self = this;
            var opt = self.options;

            var typeWatchOptions = {
                captureLength: 0,
                highlight: false,
                wait: 250,
                callback: function() {
                    self._updateSlider();
                }
            };

            self.startTime = $('<input>', {
                type: 'text',
                name: opt.startTimeName,
                maxlength: 5,
                value: opt.initStartTime
            }).attr('placeholder', 'hh:mm')
                .typeWatch(typeWatchOptions);

            self.endTime = $('<input>', {
                type: 'text',
                name: opt.endTimeName,
                maxlength: 5,
                value: opt.initEndTime
            }).attr('placeholder', 'hh:mm')
                .typeWatch(typeWatchOptions);

            self.element.on('keydown', 'input', function(e) {
                if ($(e.target).prop('name') === opt.startTimeName) {
                    if (e.which === K.TAB) {
                        e.preventDefault();
                        self.endTime.focus().select();
                    }
                } else if ($(e.target).prop('name') === opt.endTimeName) {
                    if (e.which === K.TAB && e.shiftKey) {
                        e.preventDefault();
                        self.startTime.focus().select();
                    }
                }
            });
        },

        _createSlider: function() {
            var self = this;
            var opt = self.options;

            self.slider = $('<span>').slider({
                range: true,
                max: 1439,  // last minute in a day
                values: [
                    self.__getTime(opt.initStartTime),
                    self.__getTime(opt.initEndTime)
                ],
                step: 5,
                start: function(e, ui) {
                    self._updateInputs(e, ui);
                },
                slide: function(e, ui) {
                    self._updateInputs(e, ui);
                    self._trigger('change', this);
                }
            });
        },

        _setOption: function(key, value) {
            if (key === 'disabled') {
                this.slider.slider(value ? 'disable' : 'enabled');
                this.startTime.prop('disabled', !!value);
                this.endTime.prop('disabled', !!value);
            }
            this._super(key, value);
        },

        _updateInputs: function(event, ui) {
            var self = this;

            self._restoreHighlight();
            self.startTime.val(self.__getTimeString(ui.values[0]));
            self.endTime.val(self.__getTimeString(ui.values[1]));
        },

        _updateSlider: function() {
            var self = this;

            self._restoreHighlight();
            if (self.validate()) {
                var sTime = self.__getTime(self.startTime.val());
                var eTime = self.__getTime(self.endTime.val());
                self.slider.slider('values', 0, sTime).slider('values', 1, eTime);
                self._trigger('change', this);
            }
        },

        _restoreHighlight: function() {
            var self = this;

            self.startTime.removeClass('hasError');
            self.endTime.removeClass('hasError');
        },

        __getTimeString: function(time) {
            var minutes = parseInt(time % 60, 10);
            var hours = parseInt((time / 60) % 24, 10);

            minutes = minutes + '';
            if (minutes.length === 1) {
                minutes = '0' + minutes;
            }

            return hours + ':' + minutes;
        },

        __getTime: function(timeString) {
            var time = timeString.split(':');
            return (Math.min(parseInt(time[0], 10), 23) * 60) + Math.min(parseInt(time[1], 10), 59);
        },

        __validateTime: function(timeString) {
            var time = timeString.split(':');
            var hours = parseInt(time[0], 10);
            var minutes = parseInt(time[1], 10);

            if (isNaN(hours) || isNaN(minutes)) {
                return false;
            }

            if (hours > 23 || minutes > 59) {
                return false;
            }

            return true;
        },

        getStartTime: function() {
            var self = this;
            return self.startTime.val();
        },

        getEndTime: function() {
            var self = this;
            return self.endTime.val();
        },

        resetRange: function() {
            var self = this;

            self.startTime.val(self.options.initStartTime);
            self.endTime.val(self.options.initEndTime);
            self._updateSlider();
        },

        setStartTime: function(time) {
            var self = this;

            self.startTime.val(time);
            self._updateSlider();
        },

        setEndTime: function(time) {
            var self = this;

            self.endTime.val(time);
            self._updateSlider();
        },

        setMaxRange: function() {
            var self = this;

            self.startTime.val('0:00');
            self.endTime.val('23:59');
            self._updateSlider();
        },

        setMinRange: function() {
            var self = this;

            self.startTime.val('0:00');
            self.endTime.val('0:00');
            self._updateSlider();
        },

        validate: function(highlight) {
            var self = this;

            var valid = true;
            var timeRe = /^\d{1,2}:\d{2}$/;
            var sTime = self.startTime.val();
            var eTime = self.endTime.val();

            if (highlight === undefined) {
                highlight = self.options.errorHighlight;
            }

            if (!sTime.match(timeRe) || !self.__validateTime(sTime)) {
                valid = false;
                if (highlight) {
                    self.startTime.addClass('hasError');
                }
            }

            if (!eTime.match(timeRe) || !self.__validateTime(eTime)) {
                valid = false;
                if (highlight) {
                    self.endTime.addClass('hasError');
                }
            }

            return valid;
        }
    });
})(jQuery);
