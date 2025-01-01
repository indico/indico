// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useRef} from 'react';
import {Manager, Popper} from 'react-popper';
import {Dropdown, Portal} from 'semantic-ui-react';

import './PopoverDropdownMenu.module.scss';

/** Dropdown "context" menu whose position is relative to the trigger. */
const PopoverDropdownMenu = ({trigger, children, onOpen, onClose, open, placement, overflow}) => {
  const triggerRef = useRef(null);
  return (
    <Manager>
      <Portal
        closeOnTriggerClick
        openOnTriggerClick
        open={open}
        onOpen={onOpen}
        onClose={onClose}
        trigger={
          <div styleName="trigger-container" ref={triggerRef}>
            {trigger}
          </div>
        }
      >
        <Popper
          placement={placement}
          modifiers={{
            // Custom Popper.js modifier
            closeWhenOutside: {
              enabled: true,
              fn: data => {
                const {hide} = data;
                if (hide) {
                  /* Have Popper.js close the pop-up when it's not visible.
                   * We defer the event so that React has time to finish
                   * its job and doesn't end up trying to update unmounted
                   * components.
                   */
                  _.defer(onClose);
                }
                return data;
              },
              order: 900,
            },
            hide: {
              enabled: !overflow,
            },
            preventOverflow: {
              enabled: !overflow,
            },
          }}
          referenceElement={triggerRef.current}
        >
          {({ref, style}) => {
            return (
              <div className="ui dropdown" styleName="dropdown-container" style={style} ref={ref}>
                <Dropdown.Menu open>{children}</Dropdown.Menu>
              </div>
            );
          }}
        </Popper>
      </Portal>
    </Manager>
  );
};

PopoverDropdownMenu.propTypes = {
  /** Trigger element (menu opens when clicked) */
  trigger: PropTypes.node.isRequired,
  /** Content of the menu (placed inside a `<Dropdown.Menu />`) */
  children: PropTypes.node.isRequired,
  /** Current state of the menu (open/closed) */
  open: PropTypes.bool,
  /** Gets called when the trigger is clicked */
  onOpen: PropTypes.func,
  /** Gets called when the menu is closed */
  onClose: PropTypes.func,
  /** Placement of the menu, relative to the trigger */
  placement: PropTypes.oneOf(
    _.flatten(['auto', 'top', 'right', 'bottom', 'left'].map(e => [e, `${e}-start`, `${e}-end`]))
  ),
  /** `true` means that the menu may overflow the container */
  overflow: PropTypes.bool,
};

PopoverDropdownMenu.defaultProps = {
  onOpen: () => {},
  onClose: () => {},
  open: false,
  placement: 'bottom-start',
  overflow: false,
};

export default React.memo(PopoverDropdownMenu);
