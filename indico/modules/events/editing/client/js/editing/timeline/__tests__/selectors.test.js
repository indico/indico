import {FinalRevisionState, InitialRevisionState} from 'indico/modules/events/editing/models';
import {processRevisions} from '../selectors';

describe('timeline selectors', () => {
  it('should aggregate actions on the same revision', () => {
    const revisions = [
      {
        id: 1,
        comments: '',
        initialState: {
          name: InitialRevisionState.new,
        },
        finalState: {
          name: FinalRevisionState.replaced,
        },
      },
      {
        id: 2,
        comments: '',
        initialState: {
          name: InitialRevisionState.ready_for_review,
        },
        finalState: {
          name: FinalRevisionState.needs_submitter_changes,
        },
      },
    ];
    const result = processRevisions(revisions);
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe(1);
    expect(result[0].items).toStrictEqual([
      expect.objectContaining({state: FinalRevisionState.replaced}),
      expect.objectContaining({state: FinalRevisionState.needs_submitter_changes}),
    ]);
  });

  it('should order revisions correctly', () => {
    const revisions = [
      {
        id: 1,
        comments: '',
        initialState: {
          name: InitialRevisionState.ready_for_review,
        },
        finalState: {
          name: FinalRevisionState.needs_submitter_confirmation,
        },
      },
      {
        id: 2,
        comments: '',
        initialState: {
          name: InitialRevisionState.needs_submitter_confirmation,
        },
        finalState: {
          name: FinalRevisionState.needs_submitter_changes,
        },
      },
      {
        id: 3,
        comments: '',
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
      expect.objectContaining({state: FinalRevisionState.needs_submitter_confirmation}),
    ]);
    expect(result[1].id).toBe(2);
    expect(result[1].items).toStrictEqual([
      expect.objectContaining({state: FinalRevisionState.needs_submitter_changes}),
    ]);
    expect(result[2].id).toBe(3);
    expect(result[2].items).toHaveLength(0);
  });
});
