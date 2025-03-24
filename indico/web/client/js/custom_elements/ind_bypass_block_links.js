// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import CustomElementBase from 'indico/custom_elements/_base';
import './ind_bypass_block_links.scss';

CustomElementBase.defineWhenDomReady(
  'ind-bypass-block-links',
  class extends CustomElementBase {
    setup() {
      const bypassBlockTargets = document.querySelectorAll('[id][data-bypass-target]');
      for (const target of bypassBlockTargets) {
        this.append(
          Object.assign(document.createElement('a'), {
            href: `#${target.id}`,
            textContent: target.dataset.bypassTarget,
          })
        );
      }
    }
  }
);
