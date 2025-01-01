// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Dropdown} from 'semantic-ui-react';

import {FinalField, unsortedArraysEqual} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import './TagInput.module.scss';

const optionPropTypes = PropTypes.shape({
  id: PropTypes.number.isRequired,
  code: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  verboseTitle: PropTypes.string.isRequired,
  color: PropTypes.string.isRequired,
});

/**
 * A dropdown which allows tags to be searched and added
 */
function TagInput({onChange, value, placeholder, options}) {
  return (
    <Dropdown
      placeholder={placeholder}
      styleName="tag-input"
      fluid
      multiple
      search
      selection
      value={value}
      options={options.map(({id, verboseTitle, color}) => ({
        value: id,
        text: verboseTitle,
        key: id,
        color,
      }))}
      onChange={(_, {value: v}) => onChange(v)}
      closeOnChange
      renderLabel={({color, text}) => ({
        color,
        content: text,
      })}
    />
  );
}

TagInput.propTypes = {
  /** Called whenever the value changes (receives array of Strings) */
  onChange: PropTypes.func.isRequired,
  /** The default (initial) value */
  value: PropTypes.arrayOf(PropTypes.number).isRequired,
  /** The text placeholder which should should up in the input box */
  placeholder: PropTypes.string,
  /** The list of options to show as valid tags */
  options: PropTypes.arrayOf(optionPropTypes).isRequired,
};

TagInput.defaultProps = {
  placeholder: Translate.string('Tag code or title...'),
};

/** final-form-compatible <TagInput /> */
export default function FinalTagInput({name, ...rest}) {
  return (
    <FinalField
      name={name}
      component={TagInput}
      format={v => v}
      parse={v => v}
      undefinedValue={[]}
      isEqual={unsortedArraysEqual}
      {...rest}
    />
  );
}

FinalTagInput.propTypes = {
  /** The field's name */
  name: PropTypes.string.isRequired,
  /** The list of options to show as valid tags */
  options: PropTypes.arrayOf(optionPropTypes).isRequired,
};
