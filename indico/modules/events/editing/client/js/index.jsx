// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import FileManager from './components/FileManager';

const data = [
  {
    id: '1',
    name: 'Source file',
    contentTypes: ['text/plain'],
    multiple: false,
    files: [{name: 'file1.txt', url: 'file1url', id: 'file1', claimed: true}],
  },
  {
    id: '2',
    name: 'PDF file',
    contentTypes: ['application/pdf'],
    multiple: false,
    files: [{name: 'file1.pdf', url: 'file1url', id: 'file1', claimed: true}],
  },
  {
    id: '3',
    name: 'Image files',
    contentTypes: ['image/png'],
    multiple: true,
    files: [{name: 'image.png', url: 'file1url', id: 'file1', claimed: true}],
  },
];

document.addEventListener('DOMContentLoaded', () => {
  ReactDOM.render(<FileManager fileTypes={data} />, document.getElementById('file-manager'));
});
