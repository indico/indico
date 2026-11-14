// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import * as Sentry from '@sentry/react';

type SentryConfig =
  | {enabled: false}
  | {
      enabled: true;
      dsn: string;
      feedback: boolean;
      replay: boolean;
      replay_error_sample_rate: number;
    };

export function initSentry(config: SentryConfig): {reduxEnhancer: unknown} {
  if (!config.enabled) {
    return {reduxEnhancer: undefined};
  }
  if (Indico.User) {
    Sentry.setUser({
      id: Indico.User.id,
      email: Indico.User.email,
      name: Indico.User.fullName,
    });
  }

  const integrations = [];
  if (config.replay) {
    integrations.push(
      Sentry.replayIntegration({
        maskAllText: false,
        blockAllMedia: false,
        networkDetailAllowUrls: [window.location.origin, '/'],
      })
    );
  }
  if (config.feedback) {
    integrations.push(
      Sentry.feedbackIntegration({
        colorScheme: 'system',
        useSentryUser: {
          name: 'name',
          email: 'email',
        },
      })
    );
  }

  Sentry.init({
    dsn: config.dsn,
    integrations,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: config.replay_error_sample_rate,
  });

  return {reduxEnhancer: Sentry.createReduxEnhancer()};
}

export const noSentry = {reduxEnhancer: null};
