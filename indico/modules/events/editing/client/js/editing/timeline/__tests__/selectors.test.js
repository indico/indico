// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {RevisionType} from 'indico/modules/events/editing/models';

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
        type: {
          name: RevisionType.new,
        },
      },
      {
        id: 2,
        comments: [],
        type: {
          name: RevisionType.replacement,
        },
      },
      {
        id: 3,
        comments: [],
        type: {
          name: RevisionType.needs_submitter_changes,
        },
      },
    ];
    const result = processRevisions(revisions);
    expect(result).toHaveLength(3);
    expect(result[0].id).toBe(1);
    expect(result[0].header).toStrictEqual(undefined);
    expect(result[0].items).toStrictEqual([expect.objectContaining({text: 'revision replaced'})]);
    expect(result[1].id).toBe(2);
    expect(result[1].header).toStrictEqual(revisionStates[RevisionType.replacement]);
    expect(result[1].items).toStrictEqual([]);
    expect(result[2].id).toBe(3);
    expect(result[2].header).toStrictEqual(revisionStates[RevisionType.needs_submitter_changes]);
    expect(result[2].items).toStrictEqual([]);
  });

  it('should order revisions', () => {
    const revisions = [
      {
        id: 1,
        comments: [],
        type: {
          name: RevisionType.ready_for_review,
        },
      },
      {
        id: 2,
        user: {
          fullName: 'Indico Janitor',
        },
        comments: [],
        type: {
          name: RevisionType.needs_submitter_confirmation,
        },
        commentHtml: 'hey',
      },
      {
        id: 3,
        comments: [],
        type: {
          name: RevisionType.changes_rejection,
        },
      },
      {
        id: 4,
        comments: [],
        type: {
          name: RevisionType.ready_for_review,
        },
      },
    ];
    const result = processRevisions(revisions);
    expect(result).toHaveLength(4);
    expect(result[0].id).toBe(1);
    expect(result[0].header).toStrictEqual(undefined);
    expect(result[0].items).toStrictEqual([]);
    expect(result[1].id).toBe(2);
    expect(result[1].header).toStrictEqual(
      revisionStates[RevisionType.needs_submitter_confirmation](result[1])
    );
    expect(result[1].commentHtml).toBe('hey');
    expect(result[1].items).toStrictEqual([]);
    expect(result[2].id).toBe(3);
    expect(result[2].header).toStrictEqual(revisionStates[RevisionType.changes_rejection]);
    expect(result[2].items).toStrictEqual([]);
    expect(result[3].id).toBe(4);
    expect(result[3].items).toHaveLength(0);
  });

  it('should render comments', () => {
    const revisions = [
      {
        id: 1,
        user: {
          fullName: 'james',
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
        type: {
          name: RevisionType.new,
        },
      },
      {
        id: 2,
        user: {
          fullName: 'service',
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
        type: {
          name: RevisionType.replacement,
        },
      },
      {
        id: 3,
        user: {
          fullName: 'john',
        },
        comments: [],
        type: {
          name: RevisionType.needs_submitter_changes,
        },
      },
    ];
    const result = processRevisions(revisions);
    expect(result).toHaveLength(3);
    expect(result[0].id).toBe(1);
    expect(result[0].header).toStrictEqual(undefined);
    expect(result[0].items).toStrictEqual([expect.objectContaining({text: 'first comment'})]);
    expect(result[1].id).toBe(2);
    expect(result[1].header).toStrictEqual(revisionStates[RevisionType.replacement]);
    expect(result[1].items).toStrictEqual([
      expect.objectContaining({text: 'my test comment'}),
      expect.objectContaining({text: 'done'}),
    ]);
  });
});
