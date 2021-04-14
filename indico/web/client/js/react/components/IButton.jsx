// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {toClasses} from 'indico/react/util';

export default class IButton extends React.PureComponent {
  static propTypes = {
    classes: PropTypes.object,
    href: PropTypes.string,
    title: PropTypes.string,
    children: PropTypes.any,
    onClick: PropTypes.func,
    highlight: PropTypes.bool,
    disabled: PropTypes.bool,
    icon: PropTypes.string,
    dropdown: PropTypes.bool,
  };

  static defaultProps = {
    classes: {},
    href: undefined,
    title: undefined,
    children: undefined,
    onClick: undefined,
    highlight: false,
    disabled: false,
    icon: '',
    dropdown: false,
  };

  render() {
    const {
      classes,
      disabled,
      highlight,
      href,
      title,
      children,
      onClick,
      icon,
      dropdown,
    } = this.props;
    const finalClasses = {...classes, 'i-button': true, disabled, highlight};

    if (icon) {
      finalClasses[`icon-${icon}`] = true;
    }

    if (dropdown) {
      finalClasses['arrow'] = true;
    }

    const attrs = {
      title,
      className: toClasses(finalClasses),
    };

    if (!disabled) {
      attrs['onClick'] = onClick;
    }

    if (this.href) {
      return (
        <a href={href} {...attrs}>
          {children}
        </a>
      );
    } else {
      return (
        <button type="button" {...attrs}>
          {children}
        </button>
      );
    }
  }
}
