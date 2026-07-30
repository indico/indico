// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export interface Speaker {
  id: number;
  email: string;
  name: string;
  first_name: string;
  last_name: string;
  speaker_photo_url: string;
  speaker_description: string | null;
  has_speaker_profile: boolean;
  speaker_socials: Record<
    string,
    {
      url: string;
      icon?: string;
    }
  >;
  affiliation: string;
}
