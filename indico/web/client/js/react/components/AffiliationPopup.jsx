// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import ReactDOM from 'react-dom';
import {Popup} from 'semantic-ui-react';

function AffiliationPopup({affiliation, context, container}) {
  // Set the initial state to open so that it is visible during
  // the first hover when the react component is being mounted
  const [open, setOpen] = useState(true);
  container.addEventListener('mouseenter', () => setOpen(true));
  container.addEventListener('mouseleave', () => setOpen(false));

  return (
    <Popup context={context} open={open}>
      <Popup.Header>{affiliation.name}</Popup.Header>
      <Popup.Content>
        <div>{affiliation.street}</div>
        <div>
          {affiliation.postcode} {affiliation.city}
        </div>
        <div>{affiliation.country_name}</div>
      </Popup.Content>
    </Popup>
  );
}

AffiliationPopup.propTypes = {
  affiliation: PropTypes.shape({
    name: PropTypes.string.isRequired,
    street: PropTypes.string,
    postcode: PropTypes.string,
    city: PropTypes.string,
    country_name: PropTypes.string,
  }).isRequired,
  context: PropTypes.instanceOf(Element).isRequired,
  container: PropTypes.instanceOf(Element).isRequired,
};

window.setupAffiliationPopup = (uuid, affiliation) => {
  const container = document.querySelector(`#affiliation-popup-container-${uuid}`);
  const context = document.querySelector(`#affiliation-popup-${uuid}`);
  let mounted = false;
  // Only mount the popup on hover in case there are multiple popups
  // on the page (e.g. in the contribution list)
  container.addEventListener('mouseenter', () => {
    if (!mounted) {
      mounted = true;
      ReactDOM.render(
        <AffiliationPopup affiliation={affiliation} container={container} context={context} />,
        context
      );
    }
  });
};
