// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import addTemplatePageURL from 'indico-url:receipts.add_template_page';
import cloneTemplateURL from 'indico-url:receipts.clone_template';
import deleteTemplateURL from 'indico-url:receipts.delete_template';
import templateURL from 'indico-url:receipts.template';
import templateListURL from 'indico-url:receipts.template_list';
import templatePreviewURL from 'indico-url:receipts.template_preview';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Link} from 'react-router-dom';
import {Button, Confirm, Icon, Label} from 'semantic-ui-react';

import {handleSubmitError} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import {targetLocatorSchema, templateSchema} from './util';

import './TemplateListPane.module.scss';

function TemplateRow({
  template: {id, type, title, owner},
  dispatch,
  setConfirmPrompt,
  targetLocator,
  inherited,
}) {
  const deleteTemplate = async () => {
    try {
      await indicoAxios.delete(deleteTemplateURL({template_id: id, ...targetLocator}));
      dispatch({type: 'DELETE_TEMPLATE', id});
    } catch (err) {
      return handleSubmitError(err);
    }
  };

  const cloneTemplate = async () => {
    try {
      const {data: clonedTemplate} = await indicoAxios.post(
        cloneTemplateURL({template_id: id, ...targetLocator})
      );
      dispatch({type: 'ADD_TEMPLATE', template: clonedTemplate});
    } catch (err) {
      return handleSubmitError(err);
    }
  };

  const typeLabel = {
    receipt: {color: 'red', text: Translate.string('Receipt')},
    certificate: {color: 'blue', text: Translate.string('Certificate')},
  }[type];

  return (
    <tr>
      <td className="i-table id-column">
        <i className="icon-agreement" />
      </td>
      <td>
        {title}
        {typeLabel && (
          <Label size="small" style={{marginLeft: '1em'}} color={typeLabel.color} basic>
            {typeLabel.text}
          </Label>
        )}
      </td>
      <td className="text-superfluous">
        {!!inherited && (
          <Translate>
            from category{' '}
            <Param
              name="title"
              value={owner.title}
              wrapper={<a href={templateListURL(owner.locator)} />}
            />
          </Translate>
        )}
      </td>
      <td styleName="template-actions">
        <div className="thin toolbar right">
          <a href={templatePreviewURL({template_id: id, ...targetLocator})}>
            <Icon name="eye" color="blue" title={Translate.string('Preview template')} />
          </a>
          {!inherited && (
            <Link
              to={templateURL({template_id: id, ...targetLocator})}
              onClick={evt => evt.target.dispatchEvent(new Event('indico:closeAutoTooltip'))}
            >
              <Icon name="edit" color="blue" title={Translate.string('Edit template')} />
            </Link>
          )}
          <Icon
            name="clone"
            color="blue"
            title={Translate.string('Clone template')}
            onClick={() => cloneTemplate(id)}
          />
          {!inherited && (
            <Icon
              name="trash"
              color="red"
              title={Translate.string('Delete template')}
              onClick={evt => {
                evt.target.dispatchEvent(new Event('indico:closeAutoTooltip'));
                setConfirmPrompt({
                  header: title,
                  content: Translate.string('Would you like to delete this template?'),
                  confirmButton: Translate.string('Yes'),
                  cancelButton: Translate.string('No'),
                  onConfirm: () => deleteTemplate(id),
                });
              }}
            />
          )}
        </div>
      </td>
    </tr>
  );
}

TemplateRow.propTypes = {
  template: templateSchema.isRequired,
  dispatch: PropTypes.func.isRequired,
  setConfirmPrompt: PropTypes.func.isRequired,
  targetLocator: targetLocatorSchema.isRequired,
  inherited: PropTypes.bool,
};

TemplateRow.defaultProps = {
  inherited: false,
};

export default function TemplateListPane({
  ownTemplates,
  inheritedTemplates,
  targetLocator,
  dispatch,
}) {
  const [confirmPrompt, setConfirmPrompt] = useState(null);
  return (
    <>
      {confirmPrompt !== null && (
        <Confirm
          open
          content={confirmPrompt.content}
          header={confirmPrompt.header}
          confirmButton={confirmPrompt.confirmButton}
          cancelButton={confirmPrompt.cancelButton}
          onConfirm={confirmPrompt.onConfirm}
          onCancel={() => setConfirmPrompt(null)}
        />
      )}
      {!!inheritedTemplates.length && (
        <section>
          <h3>
            <Translate>Inherited templates</Translate>
          </h3>
          <table className="i-table-widget">
            <tbody>
              {inheritedTemplates.map(tpl => (
                <TemplateRow
                  key={tpl.id}
                  template={tpl}
                  dispatch={dispatch}
                  setConfirmPrompt={setConfirmPrompt}
                  targetLocator={targetLocator}
                  inherited
                />
              ))}
            </tbody>
          </table>
        </section>
      )}
      <section className="custom-template-list">
        <div className="flexrow f-a-center f-j-space-between">
          <h3>
            <Translate>Custom templates</Translate>
          </h3>
          <Link to={addTemplatePageURL(targetLocator)}>
            <Button
              primary
              size="mini"
              title={Translate.string('Add a new blank receipt/certificate template')}
            >
              <Icon name="plus" />
              <Translate>Add new</Translate>
            </Button>
          </Link>
        </div>
        {ownTemplates.length ? (
          <table className="i-table-widget">
            <tbody>
              {ownTemplates.map(tpl => (
                <TemplateRow
                  key={tpl.id}
                  template={tpl}
                  dispatch={dispatch}
                  setConfirmPrompt={setConfirmPrompt}
                  targetLocator={targetLocator}
                />
              ))}
            </tbody>
          </table>
        ) : (
          <div className="italic text-not-important">
            <Translate>No templates</Translate>
          </div>
        )}
      </section>
    </>
  );
}

TemplateListPane.propTypes = {
  ownTemplates: PropTypes.arrayOf(templateSchema).isRequired,
  inheritedTemplates: PropTypes.arrayOf(templateSchema).isRequired,
  dispatch: PropTypes.func.isRequired,
  targetLocator: targetLocatorSchema.isRequired,
};
