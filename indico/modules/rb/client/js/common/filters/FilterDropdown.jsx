// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Button, Icon, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './FilterDropdown.module.scss';

function _mergeDefaults(defaults, values) {
  return Object.assign(
    ...Object.entries(values)
      .map(([key, value]) => {
        if (value === null && defaults[key] !== undefined) {
          return [key, defaults[key]];
        }
        return [key, value];
      })
      .map(([k, v]) => ({[k]: v}))
  );
}

const defaultTriggerRenderer = (title, renderedValue, counter, disabled) => (
  <Button
    primary={renderedValue !== null}
    styleName={counter ? 'filter-dropdown-button-counter' : 'filter-dropdown-button'}
    disabled={disabled}
  >
    {renderedValue === null ? title : renderedValue}
    <Icon name="angle down" />
  </Button>
);

export default class FilterDropdown extends React.Component {
  static propTypes = {
    title: PropTypes.element.isRequired,
    form: PropTypes.func.isRequired,
    renderValue: PropTypes.func.isRequired,
    renderTrigger: PropTypes.func,
    setGlobalState: PropTypes.func.isRequired,
    initialValues: PropTypes.object,
    defaults: PropTypes.object,
    counter: PropTypes.bool,
    open: PropTypes.bool,
    onOpen: PropTypes.func.isRequired,
    onClose: PropTypes.func.isRequired,
    disabled: PropTypes.bool,
  };

  static defaultProps = {
    initialValues: {},
    defaults: {},
    renderTrigger: defaultTriggerRenderer,
    counter: false,
    open: false,
    disabled: false,
  };

  state = {};

  static getDerivedStateFromProps(props, prevState) {
    const prevProps = prevState.prevProps;
    const {defaults, initialValues, renderValue} = props;
    const fieldValues = _mergeDefaults(defaults, initialValues);
    const renderedValue = renderValue(initialValues);

    if (!_.isEqual(prevProps, props)) {
      return {
        ...prevState,
        fieldValues,
        renderedValue,
        prevProps: props,
      };
    } else {
      return {
        fieldValues,
        renderedValue,
        ...prevState,
        prevProps: props,
      };
    }
  }

  setFieldValue = (field, value) => {
    // return promise that resolves only after the
    // state is properly set
    return new Promise(resolve => {
      // Do incremental state updates, to avoid working
      // on an outdated state (consecutive calls)
      this.setState(
        prevState => ({
          ...prevState,
          fieldValues: {
            ...prevState.fieldValues,
            [field]: value,
          },
        }),
        () => {
          resolve();
        }
      );
    });
  };

  resetFields(fieldValues) {
    this.setState({
      fieldValues,
    });
  }

  setRenderedValue = fieldValues => {
    const {renderValue} = this.props;
    const renderedValue = renderValue(fieldValues);
    this.setState({
      renderedValue,
    });
  };

  hasValuesChanged = () => {
    const {initialValues} = this.props;
    const {fieldValues} = this.state;
    return !_.isEqual(initialValues, fieldValues);
  };

  handleClose = () => {
    const {onClose, setGlobalState} = this.props;
    const {fieldValues} = this.state;
    if (this.hasValuesChanged()) {
      this.setRenderedValue(fieldValues);
      setGlobalState(fieldValues);
    }
    onClose();
  };

  handleOpen = () => {
    const {onOpen} = this.props;
    onOpen();
  };

  render() {
    const {title, form, renderTrigger, counter, open, onClose, disabled} = this.props;
    const {renderedValue, fieldValues} = this.state;

    return (
      <Popup
        position="bottom left"
        styleName="filter-dropdown"
        style={{maxWidth: 'unset'}}
        trigger={renderTrigger(title, renderedValue, counter, disabled)}
        on="click"
        open={open}
        onClose={onClose}
        onOpen={this.handleOpen}
      >
        {form(fieldValues, this.setFieldValue, this.handleClose)}
        <Button.Group size="small" floated="right" styleName="filter-dropdown-actions">
          <Button
            content={Translate.string('Apply', 'Filters')}
            onClick={this.handleClose}
            disabled={!this.hasValuesChanged()}
            positive
            compact
          />
          <Button content={Translate.string('Cancel')} onClick={onClose} compact />
        </Button.Group>
      </Popup>
    );
  }
}
