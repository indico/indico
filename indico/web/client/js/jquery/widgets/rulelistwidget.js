// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

import {$T} from 'indico/utils/i18n';

(function($) {
  function _listValue(option) {
    if (option === '') {
      return [];
    } else {
      const parsedValue = parseInt(option, 10);
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
      containerElement: null, // the actual widget containing element
      conditionChoices: {}, // specification of all possible condition values
      conditionTypes: [], // condition types, in order
    },

    _renderRuleCondition(ruleContext, condition) {
      const self = this;

      const $select = $('<select>')
        .append(
          condition.options.map(elem => {
            const optionTitle = elem[1];
            const id = elem[0];
            return $('<option>', {
              value: id,
            }).text(optionTitle);
          })
        )
        .on('change', function() {
          self._optionSelected(ruleContext, condition, $(this).val());
          self.element.trigger('change');
        });

      if (condition.required) {
        const $opt = $('<option>', {
          value: '',
          text: $T.gettext('Select an option'),
        });
        $select.prepend($opt).val('');
        $opt.prop('disabled', true);
      }

      const $html = $('<div>', {
        class: 'rule-condition',
      }).attr('data-condition', condition.value);

      if (condition.labelText) {
        $html.append($('<label>').text(condition.labelText));
      }
      return $html.append($select);
    },

    _optionSelected(ruleContext, condition, newOption) {
      ruleContext.rule[condition.value] = _listValue(newOption);
      this._checkConditionIncompatibility(ruleContext);
      this.element.trigger('change');
    },

    _onChange() {
      // Simplify rule data by removing "field: any"
      this.ruleData.forEach(rule => {
        Object.keys(rule).forEach(k => {
          if (_.isEqual(rule[k], ['*'])) {
            delete rule[k];
          }
        });
      });

      this.element.val(JSON.stringify(this.ruleData));
    },

    _checkConditionIncompatibility(ruleContext) {
      ruleContext.$element.find('.rule-condition').show();

      this.conditionSpec.forEach(condition => {
        const $condition = _findConditionByName(ruleContext, condition.value);
        const newOption = $condition.find('select').val();

        if (condition.compatibleWith) {
          const compatibleConditions = condition.compatibleWith[newOption];
          ruleContext.$element.find('.rule-condition').each(function() {
            const $this = $(this);
            const conditionName = $this.data('condition');
            if (this === $condition.get(0)) {
              return;
            }
            if (compatibleConditions?.includes(conditionName)) {
              $this.show();
            } else {
              $this.hide();
              delete ruleContext.rule[conditionName];
            }
          });
        }
      });
    },

    _setConditionOption(ruleContext, conditionName, value) {
      const $condition = _findConditionByName(ruleContext, conditionName);
      const $select = $condition.find('select');
      const isRequired = this.options.conditionChoices[conditionName].required;

      if (!isRequired && value === undefined) {
        // if the condition is not required, we can set a default (normally 'any')
        value = this.options.conditionChoices[conditionName].options[0][0];
      }

      if (value !== undefined) {
        $select.val(_optionValue(value));
      }
    },

    _checkPlaceholder() {
      const $placeholder = this.options.containerElement.find('.no-rules-placeholder');
      $placeholder.toggle(!this.ruleData.length);
    },

    _addRule($ruleList, rule) {
      const self = this;
      const ruleContext = {
        $element: $('<li>', {class: 'rule'}),
        rule,
      };
      const $removeButton = $('<a>', {class: 'i-link icon-remove rule-remove-button'});

      ruleContext.$element
        .append(
          this.conditionSpec.map(condition => self._renderRuleCondition(ruleContext, condition)),
          $removeButton
        )
        .appendTo($ruleList);

      ruleContext.$element.data('ruleContext', ruleContext);

      this.conditionSpec.forEach(condition => {
        self._setConditionOption(ruleContext, condition.value, rule[condition.value]);
      });
      this._checkConditionIncompatibility(ruleContext);
      this._checkPlaceholder();
      this.element.trigger('change');
    },

    _removeRule($elem) {
      const rule = $elem.data('ruleContext').rule;
      this.ruleData = _.without(this.ruleData, _.find(this.ruleData, _.partial(_.isEqual, rule)));
      $elem.remove();
      this._checkPlaceholder();
      this.element.trigger('change');
    },

    _addNewRule($ruleList) {
      const newRule = {};
      this.ruleData.push(newRule);
      this._addRule($ruleList, newRule);
    },

    _create() {
      const self = this;
      const $container = this.options.containerElement;
      const $addNewRuleButton = $container.find('.js-add-new-rule');
      const $ruleList = this.options.containerElement.find('.rule-list');

      this.ruleData = JSON.parse(this.element.val());

      this.conditionSpec = this.options.conditionTypes.map(type => {
        const item = self.options.conditionChoices[type];
        item['value'] = type;
        return item;
      });

      $addNewRuleButton.on('click', e => {
        self._addNewRule($ruleList);
        e.preventDefault();
      });

      $container.on('click', '.rule-remove-button', function() {
        const $elem = $(this).closest('.rule');
        self._removeRule($elem);
      });

      // Initialize widget using rule data from field
      this.ruleData.forEach(rule => {
        self._addRule($ruleList, rule);
      });

      this.element.on('change', this._onChange.bind(this));
    },
  });
})(jQuery);
