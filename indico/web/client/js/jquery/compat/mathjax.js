// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'mathjax';
import '../utils/pagedown_mathjax';

// pretend this is not an "unpacked" setup
MathJax.isPacked = true;
// the default values for these paths use isPacked before we can set it
MathJax.OutputJax.fontDir = '[MathJax]/fonts';
MathJax.OutputJax.imageDir = '[MathJax]/images';
