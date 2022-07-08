// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {Translate} from 'indico/react/i18n';

export default function DescriptionTranslationFields({languages, counter}) {
  const options = [];
  for (const lang in languages) {
    let text = languages[lang][1][0];
    if (languages[lang][1][2]) {
      const country = ` (${languages[lang][1][1]})`;
      text = `${text} ${country}`;
    }
    options.push(
      <option key={lang} value={languages[lang][0]}>
        {text}
      </option>
    );
  }
  const languageName = `description_translation_languages-${counter}`;
  const translationName = `description_translation_values-${counter}`;
  let counterText = '';
  if (counter >= 1) {
    counterText = ` ${counter + 1}`;
  }
  return (
    <div>
      <div className="form-group">
        <Translate as="label" className="form-label form-label-middle">
          {`New language${counterText}`}
        </Translate>
        <div className="form-field">
          <select className="description-language-select" name={languageName}>
            {options}
          </select>
        </div>
      </div>
      <div className="form-group">
        <Translate as="label" className="form-label form-label-middle">
          {`New translation${counterText}`}
        </Translate>
        <div className="form-field">
          <textarea name={translationName} rows={5} />
        </div>
      </div>
    </div>
  );
}

DescriptionTranslationFields.propTypes = {
  languages: PropTypes.array.isRequired,
  counter: PropTypes.number.isRequired,
};
