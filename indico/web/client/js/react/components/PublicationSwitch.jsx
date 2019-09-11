import publicationURL from 'indico-url:contributions.manage_publication';

import React, {useState, useEffect} from 'react';
import PropTypes from 'prop-types';
import {Header, Modal, Button, Checkbox} from 'semantic-ui-react';
import indicoAxios, {handleAxiosError} from 'indico/utils/axios';

export default function PublicationSwitch({confId}) {
  const [published, setPublished] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    const fetchPublicationSetting = async () => {
      let response;
      try {
        response = await indicoAxios.get(publicationURL({confId}));
        setPublished(response.data.published);
      } catch (error) {
        handleAxiosError(error);
      }
    };
    fetchPublicationSetting();
  }, [confId]);

  const publish = shouldPublish => {
    const updatePublicationSetting = async () => {
      try {
        if (shouldPublish) {
          await indicoAxios.put(publicationURL({confId}));
        } else {
          await indicoAxios.delete(publicationURL({confId}));
        }
        setPublished(shouldPublish);
      } catch (error) {
        handleAxiosError(error);
      }
    };
    updatePublicationSetting();
  };

  return (
    <Modal
      open={modalOpen}
      onClose={() => setModalOpen(false)}
      size="tiny"
      trigger={
        <Checkbox
          label={published ? 'Published' : 'Draft'}
          toggle
          onClick={() => setModalOpen(true)}
          checked={published}
        />
      }
      closeIcon
    >
      <Header content={!published ? 'Publish Contributions' : 'Unpublish Contributions'} />
      <Modal.Content>
        {published && <p>Are you sure you want to set draft mode?</p>}
        {!published && <p>Are you sure you want to publish contributions?</p>}
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={() => setModalOpen(false)}>No</Button>
        <Button
          color="blue"
          onClick={() => {
            publish(!published);
            setModalOpen(false);
          }}
        >
          Yes
        </Button>
      </Modal.Actions>
    </Modal>
  );
}

PublicationSwitch.propTypes = {
  confId: PropTypes.number.isRequired,
};
