// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export function normalizeSearchText(value: string): string {
  return value.toLowerCase().replace(/[\p{P}\s]/gu, '');
}
