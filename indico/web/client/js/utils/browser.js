// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/**
 * Download data generated locally or retrieved through AJAX as a file.
 *
 * @param {String} fileName
 * @param {String} data - Raw data obtained from the server
 */
export function downloadBlob(fileName, data) {
  const blob = new Blob([data]);
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.href = url;
  link.download = fileName;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
