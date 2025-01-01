// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous, import/no-commonjs */

function getMathJaxSource() {
  const dist = 'dist/js/mathjax/es5';
  const isStatic = JSON.parse(document.documentElement.dataset.staticSite);
  return isStatic ? `static/${dist}` : `${Indico.Urls.Base}/${dist}`;
}

window.MathJax = {
  loader: {
    paths: {
      // path from which MathJax dynamically loads components at runtime
      mathjax: getMathJaxSource(),
    },
  },
  startup: {
    typeset: false,
    elements: [],
  },
  options: {
    enableMenu: true,
    menuOptions: {
      settings: {
        zoom: 'None',
        ctrl: false,
        alt: false,
        cmd: false,
        shift: false,
        zscale: '200%',
        texHints: true,
      },
    },
    skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
    ignoreHtmlClass: 'asciimath2jax_ignore',
    processHtmlClass: 'asciimath2jax_process',
    safeOptions: {
      allow: {
        URLs: 'safe',
        classes: 'none',
        cssIDs: 'none',
        styles: 'none',
      },
      safeProtocols: {
        http: true,
        https: true,
        mailto: true,
        file: false,
        javascript: false,
        data: false,
      },
    },
  },
  tex: {
    packages: {
      '[+]': ['ams', 'html'],
      '[-]': ['require', 'autoload'], // Prevent loading packages which we did not explicitly add
    },
    inlineMath: [['$', '$']],
    displayMath: [['$$', '$$']],
    processEscapes: false,
    processEnvironments: true,
    processRefs: true,
    tagSide: 'right',
    tagIndent: '.8em',
    multlineWidth: '85%',
    tags: 'none',
    useLabelIds: true,
  },
};

// Based on this tutorial:
// https://github.com/mathjax/MathJax-demos-web/blob/master/custom-component/custom-component.html.md

//
//  Initialize the MathJax startup code
//
require('mathjax-full/components/src/startup/lib/startup.js');

//
//  Get the loader module and indicate the modules that
//  will be loaded by hand below
//
const {Loader} = require('mathjax-full/js/components/loader.js');
Loader.preLoad(
  'loader',
  'startup',
  'core',
  'input/tex-base',
  '[tex]/ams',
  '[tex]/html',
  'output/chtml',
  'output/chtml/fonts/tex.js',
  'ui/menu',
  'ui/safe' // https://docs.mathjax.org/en/latest/web/typeset.html#typesetting-user-supplied-content
);

//
// Load the components that we want to combine into one component
// (the ones listed in the preLoad() call above)
//
require('mathjax-full/components/src/core/core.js');

require('mathjax-full/components/src/input/tex-base/tex-base.js');
require('mathjax-full/components/src/input/tex/extensions/ams/ams.js');
require('mathjax-full/components/src/input/tex/extensions/html/html.js');
require('mathjax-full/components/src/output/chtml/chtml.js');
require('mathjax-full/components/src/output/chtml/fonts/tex/tex.js');
require('mathjax-full/components/src/ui/menu/menu.js');
require('mathjax-full/components/src/ui/safe/safe.js');

//
// Loading this component will cause all the normal startup
//   operations to be performed when this component is loaded
//
require('mathjax-full/components/src/startup/startup.js');

require('../utils/pagedown_mathjax');
