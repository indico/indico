// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useMemo, useRef, useState} from 'react';

import {Translate} from 'indico/react/i18n';

const linkShape = {
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
};

export default function WTFLinkListField({fieldId}) {
  const storageField = useMemo(() => document.getElementById(fieldId), [fieldId]);
  const initialLinks = storageField.value ? JSON.parse(storageField.value) : [];
  const [links, setLinks] = useState(
    initialLinks.length === 0 ? [{title: '', url: ''}] : initialLinks
  );

  useEffect(() => {
    storageField.value = JSON.stringify(links);
    storageField.dispatchEvent(new Event('change', {bubbles: true}));
  }, [storageField, links]);

  const handleChange = (idx, field, value) => {
    const newLinks = [...links];
    newLinks[idx][field] = value;
    setLinks(newLinks);
  };

  const addURL = () => setLinks([...links, {title: '', url: ''}]);

  let linksTable = null;
  // Values array should never be empty
  if (links.length === 1) {
    linksTable = (
      <div style={{marginBottom: '0.5em'}}>
        <input
          type="url"
          name="url"
          placeholder={Translate.string('URL')}
          onChange={evt => handleChange(0, 'url', evt.target.value)}
          value={links[0].url}
        />
      </div>
    );
  } else {
    const makeOnChange = idx => (field, value) => handleChange(idx, field, value);
    const makeOnDelete = idx => () => setLinks(links.filter((link, i) => i !== idx));

    linksTable = (
      <table className="i-table-widget">
        <tbody>
          {links.map((link, idx) => (
            <Link
              // eslint-disable-next-line react/no-array-index-key
              key={idx}
              onChange={makeOnChange(idx)}
              onDelete={makeOnDelete(idx)}
              title={link.title}
              url={link.url}
            />
          ))}
        </tbody>
      </table>
    );
  }
  return (
    <div className="multiple-items-widget">
      {linksTable}
      <button type="button" className="js-add-row i-button icon-plus" onClick={addURL}>
        <Translate>Add</Translate>
      </button>
    </div>
  );
}

WTFLinkListField.propTypes = {
  fieldId: PropTypes.string.isRequired,
};

function Link({onChange, onDelete, title, url}) {
  const clearRef = useRef(null);
  const makeOnChange = field => evt => onChange(field, evt.target.value);
  const handleDelete = () => {
    onDelete();
    clearRef.current.dispatchEvent(new Event('indico:closeAutoTooltip'));
  };

  return (
    <tr>
      <td>
        <input
          type="text"
          name="title"
          placeholder={Translate.string('Title')}
          onChange={makeOnChange('title')}
          value={title}
          required
        />
      </td>
      <td>
        <input
          type="url"
          name="url"
          placeholder={Translate.string('URL')}
          onChange={makeOnChange('url')}
          value={url}
          required
        />
      </td>
      <td className="js-action-col">
        <a
          ref={clearRef}
          className="icon-remove remove-row"
          title={Translate.string('Remove row')}
          onClick={handleDelete}
        />
      </td>
    </tr>
  );
}

Link.propTypes = {
  onChange: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  ...linkShape,
};
