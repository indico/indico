// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import countriesURL from 'indico-url:users.api_countries';

import PropTypes from 'prop-types';
import React from 'react';
import {Dropdown} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

const isoToFlag = code =>
  String.fromCodePoint(...code.split('').map(c => c.charCodeAt(0) + 0x1f1a5));

let countriesPromise = null;

function useCountries() {
  const [countries, setCountries] = React.useState(null);
  React.useEffect(() => {
    if (!countriesPromise) {
      countriesPromise = indicoAxios
        .get(countriesURL({}))
        .then(({data}) => data)
        .catch(error => {
          countriesPromise = null;
          handleAxiosError(error);
        });
    }
    countriesPromise.then(setCountries);
  }, []);
  return countries;
}

export function FinalCountryDropdown({name, ...rest}) {
  return <FinalField name={name} component={CountryDropdown} {...rest} />;
}

FinalCountryDropdown.propTypes = {
  name: PropTypes.string.isRequired,
};

export default function CountryDropdown({value, onChange, fluid}) {
  const countries = useCountries();

  return (
    <Dropdown
      fluid={fluid}
      search
      selection
      clearable
      value={value}
      options={(countries ?? []).map(([code, name]) => ({
        key: code,
        value: code,
        text: `${isoToFlag(code)} ${name}`,
      }))}
      onChange={(_, {value: v}) => onChange(v)}
      placeholder={Translate.string('Select a country...')}
      loading={!countries}
      disabled={!countries}
    />
  );
}

CountryDropdown.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  fluid: PropTypes.bool,
};

CountryDropdown.defaultProps = {
  fluid: false,
};
