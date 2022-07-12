// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';

import {Translate} from 'indico/react/i18n';

export default function TitleTranslation({languages}) {
  const [fieldList, setFieldList] = useState([]);
  const addFields = () => {
    setFieldList([...fieldList, 'field']);
  };
  const languageOptions = [];
  for (const lang in languages) {
    let text = languages[lang][1][0];
    if (languages[lang][1][2]) {
      const country = ` (${languages[lang][1][1]})`;
      text = `${text} ${country}`;
    }
    languageOptions.push(
      <option key={lang} value={languages[lang][0]}>
        {text}
      </option>
    );
  }
  return (
    <div>
      {fieldList.map((_, index) => (
        <div key={index}>
          <div className="form-group">
            <label className="form-label form-label-middle">
              <Translate>New language</Translate>
              {index >= 1 && <span> {index + 1}</span>}
            </label>
            <div className="form-field">
              <select
                className="title-language-select"
                name={`title_translation_languages-${index}`}
              >
                {languageOptions}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label className="form-label form-label-middle">
              <Translate>New translation</Translate>
              {index >= 1 && <span> {index + 1}</span>}
            </label>
            <div className="form-field">
              <input type="text" name={`title_translation_values-${index}`} />
            </div>
          </div>
        </div>
      ))}
      <div className="form-group">
        <div className="form-label" />
        <div className="form-field">
          <a className="i-button icon-edit" onClick={addFields}>
            <Translate>Translate title to another language</Translate>
          </a>
        </div>
      </div>
    </div>
  );
}

TitleTranslation.propTypes = {
  languages: PropTypes.array.isRequired,
};
