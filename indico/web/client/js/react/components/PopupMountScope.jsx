// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {createContext, useCallback, useContext, useState} from 'react';
import {Popup} from 'semantic-ui-react';

export const PopupMountContext = createContext(null);

export function usePopupMountNode() {
  return useContext(PopupMountContext);
}

/** Mount descendant popups inside the enclosing dialog. */
export function PopupMountScope({children}) {
  const [mountNode, setMountNode] = useState(null);
  const setMarker = useCallback(node => setMountNode(node), []);

  return (
    <PopupMountContext.Provider value={mountNode}>
      <div ref={setMarker} data-popup-mount />
      {children}
    </PopupMountContext.Provider>
  );
}

PopupMountScope.propTypes = {
  children: PropTypes.node.isRequired,
};

/** Semantic UI popup contained by the nearest PopupMountScope, when present. */
export function ContainedPopup(props) {
  const mountNode = usePopupMountNode();
  return <Popup {...props} mountNode={mountNode || undefined} />;
}

ContainedPopup.propTypes = Popup.propTypes;
