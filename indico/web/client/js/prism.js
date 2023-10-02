// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// Add syntax highglighting for TinyMCE code samples
// https://www.tiny.cloud/docs/tinymce/6/codesample/#using-prismjs-on-your-web-page

import Prism from 'prismjs';
import 'prismjs/themes/prism.css';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-csharp';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-ruby';
import 'prismjs/components/prism-markup-templating'; // dependency for prism-php
import 'prismjs/components/prism-php';

Prism.highlightAll();
