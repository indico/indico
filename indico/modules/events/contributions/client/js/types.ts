// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export interface Contribution {
  id: number;
  friendly_id: number;
  title: string;
  code: string;
  description: string;
  start_dt: string | null;
  end_dt: string | null;
  url?: string;
  edit_url?: string;
}

export type ContributionRecord = Record<string, Contribution>;
