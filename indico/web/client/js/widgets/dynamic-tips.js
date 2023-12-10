// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {domReady} from 'indico/utils/domstate';
import 'indico/custom_elements/ind_with_tooltip';

domReady.then(() => {
  document.querySelectorAll('template[data-tooltip-for]').forEach(template => {
    const target = document.getElementById(template.dataset.tooltipFor);
    if (!target) {
      return;
    }
    const tooltip = Object.assign(document.createElement('ind-with-tooltip'), {
      orientation: 'horizontal',
      innerHTML: `<div data-tip-content>${template.innerHTML}</div>`,
    });
    target.replaceWith(tooltip);
    tooltip.append(target);
  });
});
