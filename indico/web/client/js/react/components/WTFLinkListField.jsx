// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useMemo, useState, useEffect} from 'react';

import {Translate} from 'indico/react/i18n';

export default function WTFLinkListField({fieldId, wrapperId, initialLinks}) {
  const parentElement = useMemo(() => document.getElementById(wrapperId), [wrapperId]);
  const [links, setLinks] = useState(
    initialLinks.length === 0
      ? [{id: 0, title: '', url: ''}]
      : initialLinks.map((value, index) => ({
          id: index,
          title: value.title,
          url: value.url,
        }))
  );

  // Trigger change only after the DOM has changed
  useEffect(() => {
    parentElement.dispatchEvent(new Event('change', {bubbles: true}));
  }, [links, parentElement]);

  const handleChange = (id, field) => () => {
    const idx = links.findIndex(link => link.id === id);
    const newLinks = [...links];
    newLinks[idx][field] = document.getElementById(`${id}-${field}`).value;
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
          id={`${links[0].id}-url`}
          placeholder={Translate.string('URL')}
          onChange={handleChange(links[0].id, 'url')}
          value={links[0].url}
        />
      </div>
    );
  } else {
    const removeURL = id => () => {
      setLinks(links.filter(link => link.id !== id));
    };

    linksTable = (
      <table className="i-table-widget">
        <tbody>
          {links.map(link => (
            <tr key={link.id}>
              <td>
                <input
                  type="text"
                  id={`${link.id}-title`}
                  placeholder={Translate.string('Title')}
                  onChange={handleChange(link.id, 'title')}
                  value={link.title}
                  required
                />
              </td>
              <td>
                <input
                  type="url"
                  id={`${link.id}-url`}
                  placeholder={Translate.string('URL')}
                  onChange={handleChange(link.id, 'url')}
                  value={link.url}
                  required
                />
              </td>
              <td className="js-action-col">
                <a
                  className="icon-remove remove-row"
                  title={Translate.string('Remove row')}
                  onClick={removeURL(link.id)}
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
        value={JSON.stringify(getProcessedLinks())}
      />
    </div>
  );
}

WTFLinkListField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  wrapperId: PropTypes.string.isRequired,
  initialLinks: PropTypes.arrayOf(
    PropTypes.shape({
      title: PropTypes.string.isRequired,
      url: PropTypes.string.isRequired,
    })
  ).isRequired,
};
