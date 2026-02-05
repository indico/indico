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
  speaker_description: string | null;
  speaker_photo_url: string | null;
  speaker_facebook: string | null;
  speaker_github: string | null;
  speaker_linkedin: string | null;
  speaker_webpage: string | null;
  avatar_url: string;
  affiliation: string;
}
