// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useRef, useState} from 'react';

import {Checkbox} from 'indico/react/components';
import {useVerticalArrowNavigation} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';

import './SearchBox.module.scss';

function CategoryOption({keyword, scopeLabel, formAction}) {
  return (
    <li styleName="search-type-option">
      <button type="submit" formAction={formAction} data-stop>
        <Translate>
          Find "<Param name="keyword" value={keyword} />" in{' '}
          <Param wrapper={<span styleName="search-scope" />} name="scope" value={scopeLabel} />
        </Translate>
      </button>
    </li>
  );
}

CategoryOption.propTypes = {
  keyword: PropTypes.string.isRequired,
  scopeLabel: PropTypes.string.isRequired,
  formAction: PropTypes.string,
};

CategoryOption.defaultProps = {
  formAction: undefined,
};

function AdminOverrideOption() {
  // Keeps focus within the search box widget as we rely on
  // focus state to keep the popup open.
  const focusCheckbox = evt => {
    const label = evt.currentTarget;
    // Focusout fires *after* this event and it would annul the
    // `.focus()` call below, so we need to wait for it.
    requestAnimationFrame(() => label.querySelector('input').focus());
  };

  return (
    <li styleName="admin-check">
      <label onPointerDown={focusCheckbox}>
        <Translate as="span" styleName="admin-label">
          Admin
        </Translate>
        <span styleName="admin-check">
          <Checkbox name="admin_override_enabled" value="true" data-stop />
          <Translate as="span">Skip access checks</Translate>
        </span>
      </label>
    </li>
  );
}

export default function SearchBox({options, defaultUrl, isAdmin}) {
  const [keyword, setKeyword] = useState('');
  const searchOptions = [];
  const formRef = useRef();
  const inputRef = useRef();

  if (keyword) {
    for (const opt of options) {
      searchOptions.push(<CategoryOption key={opt.scopeLabel} keyword={keyword} {...opt} />);
    }
  }

  if (isAdmin) {
    searchOptions.push(<AdminOverrideOption key="override" />);
  }

  const handleKeywordChange = ev => {
    setKeyword(ev.target.value.trim());
  };

  useVerticalArrowNavigation(formRef, inputRef);

  return (
    <form ref={formRef} action={defaultUrl} styleName="search-box" role="application">
      <label styleName="field">
        <Translate as="span">Search (use the arrow keys to select search options).</Translate>
        <input
          ref={inputRef}
          type="text"
          name="q"
          onChange={handleKeywordChange}
          value={keyword}
          autoComplete="off"
          required
          data-stop
        />
      </label>
      <div styleName="options">{searchOptions}</div>
    </form>
  );
}

SearchBox.propTypes = {
  defaultUrl: PropTypes.string.isRequired,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      scopeLabel: PropTypes.string.isRequired,
      formAction: PropTypes.string,
    })
  ).isRequired,
  isAdmin: PropTypes.bool.isRequired,
};
