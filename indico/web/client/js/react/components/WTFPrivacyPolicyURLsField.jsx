// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useMemo, useState, useEffect} from 'react';

import {Translate} from 'indico/react/i18n';

export default function WTFPrivacyPolicyURLsField({fieldId, wrapperId, initialValues}) {
  const parentElement = useMemo(() => document.getElementById(wrapperId), [wrapperId]);
  const [values, setValues] = useState(
    initialValues.length === 0
      ? [{id: 0, title: '', url: ''}]
      : initialValues.map((value, index) => ({
          id: index,
          title: value.title,
          url: value.url,
        }))
  );

  // Trigger change only after the DOM has changed
  useEffect(() => {
    parentElement.dispatchEvent(new Event('change', {bubbles: true}));
  }, [values, parentElement]);

  const handleChange = (id, field) => () => {
    const idx = values.findIndex(value => value.id === id);
    const newValues = [...values];
    newValues[idx][field] = document.getElementById(`${id}-${field}`).value;
    setValues(newValues);
  };

  const getProcessedValues = () => {
    const newValues = values.filter(value => value.title !== '' || value.url !== '');
    if (newValues.length === 1) {
      return [{title: '', url: newValues[0].url}];
    }
    return newValues.map(value => ({
      title: value.title,
      url: value.url,
    }));
  };

  const addURL = () => {
    setValues([...values, {id: values.at(-1).id + 1, title: '', url: ''}]);
  };

  let linksTable = null;
  // Values array should never be empty
  if (values.length === 1) {
    linksTable = (
      <div style={{marginBottom: '0.5em'}}>
        <input
          type="text"
          id={`${values[0].id}-url`}
          placeholder={Translate.string('URL')}
          onChange={handleChange(values[0].id, 'url')}
          value={values[0].url}
        />
      </div>
    );
  } else {
    const removeURL = id => () => {
      setValues(values.filter(value => value.id !== id));
    };

    linksTable = (
      <table className="i-table-widget">
        <tbody>
          {values.map(value => (
            <tr key={value.id}>
              <td>
                <input
                  type="text"
                  id={`${value.id}-title`}
                  placeholder={Translate.string('Title')}
                  onChange={handleChange(value.id, 'title')}
                  value={value.title}
                  required
                />
              </td>
              <td>
                <input
                  type="url"
                  id={`${value.id}-url`}
                  placeholder={Translate.string('URL')}
                  onChange={handleChange(value.id, 'url')}
                  value={value.url}
                  required
                />
              </td>
              <td className="js-action-col">
                <a
                  className="icon-remove remove-row"
                  title={Translate.string('Remove row')}
                  onClick={removeURL(value.id)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }
  return (
    <div>
      <div className="multiple-items-widget">
        {linksTable}
        <button type="button" className="js-add-row i-button icon-plus" onClick={addURL}>
          <Translate>Add</Translate>
        </button>
      </div>
      <input
        type="hidden"
        id={fieldId}
        name={fieldId}
        value={JSON.stringify(getProcessedValues())}
      />
    </div>
  );
}

WTFPrivacyPolicyURLsField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  wrapperId: PropTypes.string.isRequired,
  initialValues: PropTypes.arrayOf(
    PropTypes.shape({
      title: PropTypes.string.isRequired,
      url: PropTypes.string.isRequired,
    })
  ).isRequired,
};
