import emailAttributesURL from 'indico-url:persons.email_event_persons';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Form, Modal, Button, TextArea, Message} from 'semantic-ui-react';

import TextEditor from 'indico/react/components/TextEditor';
import {
  FinalCheckbox,
  FinalDropdown,
  FinalField,
  FinalInput,
  handleSubmitError,
} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';

const useIdSelector = selector =>
  Array.from(document.querySelectorAll(selector))
    .filter(e => e.offsetWidth > 0 || e.offsetHeight > 0)
    .map(e => +e.value);

export function EmailButton({eventId, personSelector, userSelector, roleSelector}) {
  const [open, setOpen] = useState(false);
  const personIds = useIdSelector(personSelector);
  const userIds = useIdSelector(userSelector);
  const roleIds = useIdSelector(roleSelector);

  return (
    <Modal
      onClose={() => setOpen(false)}
      onOpen={() => setOpen(true)}
      open={open}
      trigger={<Translate as={Button}>Send email</Translate>}
      closeIcon
    >
      <Translate as={Modal.Header}>Send email</Translate>
      <Modal.Content>
        <EmailForm eventId={eventId} personIds={personIds} userIds={userIds} roleIds={roleIds} />
      </Modal.Content>
    </Modal>
  );
}

EmailButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  personSelector: PropTypes.string,
  userSelector: PropTypes.string,
  roleSelector: PropTypes.string,
};

EmailButton.defaultProps = {
  personSelector: undefined,
  userSelector: undefined,
  roleSelector: undefined,
};

export function EmailForm({eventId, personIds, roleIds, userIds}) {
  const recipientData = {personId: personIds, roleId: roleIds, userId: userIds};
  const {data} = useIndicoAxios({
    url: emailAttributesURL({event_id: eventId}),
    trigger: eventId,
    options: {params: snakifyKeys(recipientData)},
  });
  const loading = !data;
  const {senders = [], recipients = [], subject, body} = data || {};

  const onSubmit = async data => {
    try {
      await indicoAxios.post(emailAttributesURL({event_id: eventId}), snakifyKeys(data), {
        params: snakifyKeys(recipientData),
      });
    } catch (err) {
      return handleSubmitError(err);
    }
  };

  const renderForm = ({handleSubmit, submitting, submitSucceeded}) => (
    <Form loading={loading} onSubmit={handleSubmit}>
      {submitSucceeded && (
        <Message positive>
          <Translate as={Message.Header}>Your email has been sent.</Translate>
          <Translate as="p">
            {Object.values(recipientData).reduce((acc, v) => acc + v.length, 0)} emails have been
            sent.
          </Translate>
        </Message>
      )}
      <Form.Field>
        <Translate as="label">From</Translate>
        <FinalDropdown
          name="fromAddress"
          scrolling
          selection
          options={senders.map(([value, text]) => ({value, text}))}
        />
      </Form.Field>
      <Form.Field>
        <Translate as="label">Subject</Translate>
        <FinalInput name="subject" />
      </Form.Field>
      <Form.Field>
        <Translate as="label">Email body</Translate>
        <FinalField name="body">
          {({input}) => (
            <TextEditor
              value={input.value}
              onChange={(_, editor) => input.onChange(editor.getData())}
            />
          )}
        </FinalField>
      </Form.Field>
      <Form.Field>
        <Translate as="label">Recipients</Translate>
        <TextArea value={recipients.join(', ')} readOnly />
      </Form.Field>
      <Form.Field>
        <Translate as="label">Send copy to me</Translate>
        <FinalCheckbox name="copyForSender" label={Translate.string('Send copy to me')} toggle />
        <Translate as="p" className="field-description">
          Send copy of each email to my mailbox
        </Translate>
      </Form.Field>
      <Translate as={Button} type="submit" disabled={submitting || submitSucceeded}>
        Send
      </Translate>
    </Form>
  );

  return (
    <FinalForm
      initialValues={{
        recipients: recipients.join(', '),
        fromAddress: senders[0] && senders[0][0],
        subject,
        body,
      }}
      onSubmit={onSubmit}
      render={renderForm}
    />
  );
}

EmailForm.propTypes = {
  eventId: PropTypes.number.isRequired,
  personIds: PropTypes.arrayOf(PropTypes.number),
  userIds: PropTypes.arrayOf(PropTypes.number),
  roleIds: PropTypes.arrayOf(PropTypes.number),
};

EmailForm.defaultProps = {
  personIds: [],
  userIds: [],
  roleIds: [],
};
