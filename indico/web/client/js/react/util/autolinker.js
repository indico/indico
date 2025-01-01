// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {findAndReplace} from 'mdast-util-find-and-replace';

function createReplacer(url) {
  return (title, ...params) => {
    return {
      type: 'link',
      title,
      url: url.replace(/\{(\d+)\}/g, m => {
        const value = [title, ...params][m[1]];
        return value === undefined || value === null ? '' : value;
      }),
      children: [{type: 'text', value: title}],
    };
  };
}

export default function AutoLinkerPlugin({rules}) {
  const replacers = rules.map(({regex, url}) => [new RegExp(regex, 'g'), createReplacer(url)]);
  return tree => {
    findAndReplace(tree, replacers, {
      ignore: ['link', 'linkReference'],
    });
  };
}
