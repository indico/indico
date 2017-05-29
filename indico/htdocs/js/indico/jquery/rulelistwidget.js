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

    function _listValue(option) {
        if (option === '') {
            return [];
        } else {
            var parsedValue = parseInt(option, 10);
            return [isNaN(parsedValue) ? option : parsedValue];
        }
    }

    function _optionValue(option) {
        if (option.length === 0) {
            return '';
        } else {
            return option[0];
        }
    }

    function _findConditionByName(ruleContext, conditionName) {
        return ruleContext.$element.find('.rule-condition').filter(function() {
            return $(this).attr('data-condition') === conditionName;
        });
    }

    $.widget('indico.rulelistwidget', {
        options: {
            containerElement: null,  // the actual widget containing element
            conditionChoices: {},  // specification of all possible condition values
            conditionTypes: []  // condition types, in order
        },

        _renderRuleCondition: function(ruleContext, condition) {
            var self = this;

            var $select = $('<select>')
                .append(_.map(condition.options, function(elem) {
                    var optionTitle = elem[1];
                    var id = elem[0];
                    return $('<option>', {
                        value: id
                    }).text(optionTitle);
                })).on('change', function() {
                    self._optionSelected(ruleContext, condition, $(this).val());
                    self.element.trigger('change');
                });

            if (condition.required) {
                $select.prepend($('<option disabled selected>', {
                    value: ''
                }).text($T.gettext('Select an option')));
            }

            var $html = $('<div>', {
                class: 'rule-condition'
            }).attr('data-condition', condition.value);

            if (condition.labelText) {
                $html.append($('<label>').text(condition.labelText));
            }
            return $html.append($select);
        },

        _optionSelected: function(ruleContext, condition, newOption) {
            ruleContext.rule[condition.value] = _listValue(newOption);
            this._checkConditionIncompatibility(ruleContext);
            this.element.trigger('change');
        },

        _onChange: function() {
            // Simplify rule data by removing "field: any"
            this.ruleData.forEach(function(rule) {
                _.keys(rule).forEach(function(k) {
                    if (_.isEqual(rule[k], ['*'])) {
                        delete rule[k];
                    }
                });
            });

            this.element.val(JSON.stringify(this.ruleData));
        },

        _checkConditionIncompatibility: function(ruleContext) {
            ruleContext.$element.find('.rule-condition').show();

            this.conditionSpec.forEach(function(condition) {
                var $condition = _findConditionByName(ruleContext, condition.value);
                var newOption = $condition.find('select').val();

                if (condition.compatibleWith) {
                    var compatibleConditions = condition.compatibleWith[newOption];
                    ruleContext.$element.find('.rule-condition').each(function() {
                        var $this = $(this);
                        var conditionName = $this.data('condition');
                        if (this === $condition.get(0)) {
                            return;
                        }
                        if (_.contains(compatibleConditions, conditionName)) {
                            $this.show();
                        } else {
                            $this.hide();
                            delete ruleContext.rule[conditionName];
                        }
                    });
                }
            });
        },

        _setConditionOption: function(ruleContext, conditionName, value) {
            var $condition = _findConditionByName(ruleContext, conditionName);
            var $select = $condition.find('select');
            var isRequired = this.options.conditionChoices[conditionName].required;

            if (!isRequired && value === undefined) {
                // if the condition is not required, we can set a default (normally 'any')
                value = this.options.conditionChoices[conditionName].options[0][0];
            }

            if (value !== undefined) {
                $select.val(_optionValue(value));
            }
        },

        _checkPlaceholder: function() {
            var $placeholder = this.options.containerElement.find('.no-rules-placeholder');
            $placeholder.toggle(!this.ruleData.length);
        },

        _addRule: function($ruleList, rule) {
            var self = this;
            var ruleContext = {
                $element: $('<li>', {class: 'rule'}),
                rule: rule
            };
            var $removeButton = $('<a>', {class: 'i-link icon-remove rule-remove-button'});

            ruleContext.$element.append(
                _.map(this.conditionSpec, function(condition) {
                    return self._renderRuleCondition(ruleContext, condition);
                }),
                $removeButton
            ).appendTo($ruleList);

            ruleContext.$element.data('ruleContext', ruleContext);

            this.conditionSpec.forEach(function(condition) {
                self._setConditionOption(ruleContext, condition.value, rule[condition.value]);
            });
            this._checkConditionIncompatibility(ruleContext);
            this._checkPlaceholder();
            this.element.trigger('change');
        },

        _removeRule: function($elem) {
            var rule = $elem.data('ruleContext').rule;
            this.ruleData = _.without(this.ruleData, _.find(this.ruleData, _.partial(_.isEqual, rule)));
            $elem.remove();
            this._checkPlaceholder();
            this.element.trigger('change');
        },

        _addNewRule: function($ruleList) {
            var newRule = {};
            this.ruleData.push(newRule);
            this._addRule($ruleList, newRule);
        },

        _create: function() {
            var self = this;
            var $container = this.options.containerElement;
            var $addNewRuleButton = $container.find('.js-add-new-rule');
            var $ruleList = this.options.containerElement.find('.rule-list');

            this.ruleData = JSON.parse(this.element.val());

            this.conditionSpec =  _.map(this.options.conditionTypes, function(type) {
                var item = self.options.conditionChoices[type];
                item['value'] = type;
                return item;
            });

            $addNewRuleButton.on('click', function(e) {
                self._addNewRule($ruleList);
                e.preventDefault();
            });

            $container.on('click', '.rule-remove-button', function() {
                var $elem = $(this).closest('.rule');
                self._removeRule($elem);
            });

            // Initialize widget using rule data from field
            this.ruleData.forEach(function(rule) {
                self._addRule($ruleList, rule);
            });

            this.element.on('change', this._onChange.bind(this));
        }
    });
})(jQuery);
