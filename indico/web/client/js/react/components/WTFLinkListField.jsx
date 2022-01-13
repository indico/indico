// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useRef, useState, useEffect} from 'react';

import {Translate} from 'indico/react/i18n';

const linkShape = {
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
};

export default function WTFLinkListField({fieldId, initialLinks}) {
  const hiddenInputRef = useRef(null);
  const [links, setLinks] = useState(
    initialLinks.length === 0
      ? [{id: 0, title: '', url: ''}]
      : initialLinks.map((value, index) => ({
          id: index,
          title: value.title,
          url: value.url,
        }))
  );

  useEffect(() => {
    hiddenInputRef.current.dispatchEvent(new Event('change', {bubbles: true}));
  }, [links]);

  const handleChange = (id, field, value) => {
    const newLinks = [...links];
    newLinks[links.findIndex(link => link.id === id)][field] = value;
    setLinks(newLinks);
  };

  const getProcessedLinks = () => {
    const newLinks = links.filter(link => link.title || link.url);
    if (newLinks.length === 1) {
      return [{title: '', url: newLinks[0].url}];
    }
    return newLinks.map(link => ({
      title: link.title,
      url: link.url,
    }));
  };

  const addURL = () => {
    setLinks([...links, {id: links.at(-1).id + 1, title: '', url: ''}]);
  };

  let linksTable = null;
  // Values array should never be empty
  if (links.length === 1) {
    linksTable = (
      <div style={{marginBottom: '0.5em'}}>
        <input
          type="text"
          name="url"
          placeholder={Translate.string('URL')}
          onChange={evt => handleChange(links[0].id, 'url', evt.target.value)}
          value={links[0].url}
        />
      </div>
    );
  } else {
    const makeOnChange = id => (field, value) => handleChange(id, field, value);
    const makeOnDelete = id => () => setLinks(links.filter(link => link.id !== id));

    linksTable = (
      <table className="i-table-widget">
        <tbody>
          {links.map(link => (
            <Link
              key={link.id}
              onChange={makeOnChange(link.id)}
              onDelete={makeOnDelete(link.id)}
              title={link.title}
              url={link.url}
            />
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
        ref={hiddenInputRef}
        type="hidden"
        id={fieldId}
        name={fieldId}
        value={JSON.stringify(getProcessedLinks())}
      />
    </div>
  );
}

WTFLinkListField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  initialLinks: PropTypes.arrayOf(PropTypes.shape(linkShape)).isRequired,
};

function Link({onChange, onDelete, title, url}) {
  const clearRef = useRef(null);
  const makeOnChange = field => evt => onChange(field, evt.target.value);
  const makeOnDelete = () => {
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
          onClick={makeOnDelete}
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
