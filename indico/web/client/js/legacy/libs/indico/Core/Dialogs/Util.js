// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function() {
  'use strict';

  IndicoUI.Dialogs.Util = {
    progress: function(text) {
      var dialog = new ProgressDialog(text);
      dialog.open();

      return function() {
        dialog.close();
      };
    },
  };
})();
