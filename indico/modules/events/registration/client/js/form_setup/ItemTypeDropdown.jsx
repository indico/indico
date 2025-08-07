// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Dropdown} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {getFieldRegistry} from '../form/fields/registry';

import '../../styles/regform.module.scss';

export default function ItemTypeDropdown({newItemType, inModal, onClick}) {
  const fieldRegistry = getFieldRegistry();
  const dropdownText = newItemType
    ? fieldRegistry[newItemType].title
    : Translate.string('Choose type');

  let extraProps;
  if (inModal) {
    extraProps = {
      icon: 'dropdown',
      text: dropdownText,
    };
  } else {
    extraProps = {
      icon: null,
      className: 'hide-if-locked',
      trigger: <a className="icon-plus" title={Translate.string('Add field')} />,
    };
  }

  const newItemTypeOptions = Object.entries(fieldRegistry)
    .filter(([name]) => name !== 'label')
    .map(([name, {title, icon}]) => ({
      key: name,
      value: name,
      text: title,
      icon,
    }));
  const middle = Math.ceil(newItemTypeOptions.length / 2);

  return (
    <Dropdown
      selectOnNavigation={false}
      selectOnBlur={false}
      value={newItemType}
      direction="left"
      {...extraProps}
    >
      <Dropdown.Menu>
        <DropdownItem
          value="label"
          text={fieldRegistry.label.title}
          icon={fieldRegistry.label.icon}
          centered
          onClick={onClick}
        />
        <Dropdown.Divider style={{margin: 0}} />
        <div styleName="dropdown-menu">
          <div>
            {newItemTypeOptions.slice(0, middle).map(({key, ...rest}) => (
              <DropdownItem key={key} onClick={onClick} {...rest} />
            ))}
          </div>
          <div>
            {newItemTypeOptions.slice(middle).map(({key, ...rest}) => (
              <DropdownItem key={key} onClick={onClick} {...rest} />
            ))}
          </div>
        </div>
      </Dropdown.Menu>
    </Dropdown>
  );
}

ItemTypeDropdown.propTypes = {
  newItemType: PropTypes.string,
  inModal: PropTypes.bool.isRequired,
  onClick: PropTypes.func.isRequired,
};

ItemTypeDropdown.defaultProps = {
  newItemType: null,
};

function DropdownItem({value, text, icon, centered, onClick}) {
  return (
    <div
      styleName="dropdown-item"
      style={centered ? {textAlign: 'center'} : null}
      onClick={() => onClick(value)}
    >
      <i className={`icon-${icon}`} />
      <span>{text}</span>
    </div>
  );
}

DropdownItem.propTypes = {
  value: PropTypes.string.isRequired,
  text: PropTypes.string.isRequired,
  icon: PropTypes.string.isRequired,
  centered: PropTypes.bool,
  onClick: PropTypes.func.isRequired,
};

DropdownItem.defaultProps = {
  centered: false,
};
