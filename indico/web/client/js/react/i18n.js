// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import Jed from 'jed';
import {makeComponents} from 'react-jsx-i18n';

export const bindTranslateComponents = domain => {
  const jed = new Jed({
    locale_data: window.REACT_TRANSLATIONS,
    domain,
  });
  return makeComponents(jed);
};

export const {Translate, PluralTranslate} = bindTranslateComponents('indico');
export {Singular, Plural, Param} from 'react-jsx-i18n';
