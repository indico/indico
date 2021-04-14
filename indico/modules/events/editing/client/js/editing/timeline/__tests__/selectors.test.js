// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {FinalRevisionState, InitialRevisionState} from 'indico/modules/events/editing/models';

import {processRevisions, revisionStates} from '../util';

describe('timeline selectors', () => {
  it('should describe each revision transition', () => {
    const revisions = [
      {
        id: 1,
        comments: [
          {
            id: 1,
            text: 'revision replaced',
            user: {
              fullName: 'Indico Janitor',
            },
          },
        ],
        initialState: {
          name: InitialRevisionState.new,
        },
        finalState: {
          name: FinalRevisionState.replaced,
        },
      },
      {
        id: 2,
        comments: [],
        initialState: {
          name: InitialRevisionState.ready_for_review,
        },
        finalState: {
          name: FinalRevisionState.needs_submitter_changes,
        },
      },
    ];
    const result = processRevisions(revisions);
    expect(result).toHaveLength(2);
    expect(result[0].id).toBe(1);
    expect(result[0].items).toStrictEqual([
      expect.objectContaining({text: 'revision replaced'}),
      expect.objectContaining({
        header: revisionStates.any[FinalRevisionState.replaced],
      }),
    ]);
    expect(result[1].id).toBe(2);
    expect(result[1].items).toStrictEqual([
      expect.objectContaining({
        header: revisionStates.any[FinalRevisionState.needs_submitter_changes],
      }),
    ]);
  });

  it('should order revisions', () => {
    const revisions = [
      {
        id: 1,
        comments: [],
        initialState: {
          name: InitialRevisionState.ready_for_review,
        },
        finalState: {
          name: FinalRevisionState.needs_submitter_confirmation,
        },
        commentHtml: 'hey',
      },
      {
        id: 2,
        comments: [],
        initialState: {
          name: InitialRevisionState.needs_submitter_confirmation,
        },
        finalState: {
          name: FinalRevisionState.needs_submitter_changes,
        },
      },
      {
        id: 3,
        comments: [],
        initialState: {
          name: InitialRevisionState.ready_for_review,
        },
        finalState: {
          name: FinalRevisionState.none,
        },
      },
    ];
    const result = processRevisions(revisions);
    expect(result).toHaveLength(3);
    expect(result[0].id).toBe(1);
    expect(result[0].items).toStrictEqual([
      expect.objectContaining({
        header: revisionStates.any[FinalRevisionState.needs_submitter_confirmation](result[0]),
        html: 'hey',
      }),
    ]);
    expect(result[1].id).toBe(2);
    expect(result[1].items).toStrictEqual([
      expect.objectContaining({
        header:
          revisionStates[InitialRevisionState.needs_submitter_confirmation][
            FinalRevisionState.needs_submitter_changes
          ],
      }),
    ]);
    expect(result[2].id).toBe(3);
    expect(result[2].items).toHaveLength(0);
  });

  it('should render comments', () => {
    const revisions = [
      {
        id: 1,
        editor: {
          fullName: 'service',
        },
        comments: [
          {
            id: 1,
            text: 'first comment',
            user: {
              fullName: 'Indico Janitor',
            },
          },
        ],
        initialState: {
          name: InitialRevisionState.new,
        },
        finalState: {
          name: FinalRevisionState.replaced,
        },
      },
      {
        id: 2,
        editor: {
          fullName: 'john',
        },
        comments: [
          {
            id: 1,
            text: 'my test comment',
            user: {
              fullName: 'Indico Janitor',
            },
          },
          {
            id: 2,
            text: 'done',
            user: {
              fullName: 'Indico Janitor',
            },
          },
        ],
        initialState: {
          name: InitialRevisionState.ready_for_review,
        },
        finalState: {
          name: FinalRevisionState.needs_submitter_changes,
        },
      },
    ];
    const result = processRevisions(revisions);
    expect(result).toHaveLength(2);
    expect(result[0].id).toBe(1);
    expect(result[0].items).toStrictEqual([
      expect.objectContaining({text: 'first comment'}),
      expect.objectContaining({
        header: revisionStates.any[FinalRevisionState.replaced],
        user: result[0].editor,
      }),
    ]);
    expect(result[1].id).toBe(2);
    expect(result[1].items).toStrictEqual([
      expect.objectContaining({text: 'my test comment'}),
      expect.objectContaining({text: 'done'}),
      expect.objectContaining({
        header: revisionStates.any[FinalRevisionState.needs_submitter_changes],
        user: result[1].editor,
      }),
    ]);
  });
});
