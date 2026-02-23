import React from 'react';
import {useSelector} from 'react-redux';
import {List, Modal} from 'semantic-ui-react';

import {BlockEntry, SessionBlockId} from 'indico/modules/events/timetable/types';
import {Param, Translate} from 'indico/react/i18n';

import * as selectors from './selectors';

interface TimetablePosterBlockModalProps {
  id: SessionBlockId;
  onClose: () => void;
}

export const TimetablePosterBlockModal: React.FC<TimetablePosterBlockModalProps> = ({
  id,
  onClose,
}) => {
  const block = useSelector(selectors.getCurrentDayEntries).find(
    (e): e is BlockEntry => e.id === id
  );
  return (
    <Modal size="small" onClose={onClose} defaultOpen>
      <Modal.Header>
        <Translate>
          Contributions of '
          <Param name="posterSessionBlockTitle" value={block.title} />
          '.
        </Translate>
      </Modal.Header>
      <Modal.Content as={List} divided relaxed>
        {block.children.map(c => (
          <List.Item key={c.id}>{c.title}</List.Item>
        ))}
      </Modal.Content>
    </Modal>
  );
};
