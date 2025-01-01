// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import addDefaultTemplateURL from 'indico-url:receipts.add_default_template';
import addTemplateURL from 'indico-url:receipts.add_template';
import editTemplateURL from 'indico-url:receipts.edit_template';
import getDefaultTemplateURL from 'indico-url:receipts.get_default_template';
import templateURL from 'indico-url:receipts.template';
import templateListURL from 'indico-url:receipts.template_list';

import PropTypes from 'prop-types';
import React, {useReducer, useEffect} from 'react';
import {useHistory} from 'react-router';
import {BrowserRouter as Router, Route, Switch} from 'react-router-dom';
import {Message} from 'semantic-ui-react';

import {ManagementPageBackButton} from 'indico/react/components';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {routerPathFromFlask, useNumericParam} from 'indico/react/util/routing';
import {indicoAxios} from 'indico/utils/axios';

import TemplateListPane from './TemplateListPane';
import TemplatePane from './TemplatePane';
import {defaultTemplateSchema, templateSchema} from './util';

const targetLocatorSchema = PropTypes.shape({
  event_id: PropTypes.number,
  category_id: PropTypes.number,
});

function reducer(state, action) {
  switch (action.type) {
    case 'ADD_TEMPLATE':
      return {
        ...state,
        ownTemplates: [...state.ownTemplates, action.template],
        message: Translate.string('Template "{title}" was added', {title: action.template.title}),
      };
    case 'UPDATE_TEMPLATE':
      return {
        ...state,
        ownTemplates: state.ownTemplates.map(tpl =>
          tpl.id === action.id ? {...tpl, ...action.changes} : tpl
        ),
        message: Translate.string('Template "{title}" was updated', {title: action.changes.title}),
      };
    case 'DELETE_TEMPLATE':
      return {
        ...state,
        ownTemplates: state.ownTemplates.filter(tpl => tpl.id !== action.id),
        message: Translate.string('Template deleted'),
      };
    case 'RESET_MESSAGE':
      return {
        ...state,
        message: null,
      };
    default:
      return state;
  }
}

function EditTemplatePane({templates, dispatch, targetLocator}) {
  const templateId = useNumericParam('template_id');

  const saveTemplate = async data => {
    try {
      await indicoAxios.patch(editTemplateURL({template_id: templateId, ...targetLocator}), data);
      dispatch({type: 'UPDATE_TEMPLATE', id: templateId, changes: data});
    } catch ({
      response: {
        data: {webargs_errors: errors},
      },
    }) {
      return errors;
    }
  };

  return (
    <>
      <ManagementPageBackButton url={templateListURL(targetLocator)} />
      <TemplatePane
        targetLocator={targetLocator}
        template={templates.find(tpl => tpl.id === templateId)}
        onSubmit={saveTemplate}
      />
    </>
  );
}

EditTemplatePane.propTypes = {
  dispatch: PropTypes.func.isRequired,
  targetLocator: targetLocatorSchema.isRequired,
  templates: PropTypes.arrayOf(templateSchema).isRequired,
};

function NewTemplatePane({dispatch, targetLocator, defaultTemplate}) {
  const history = useHistory();
  const {data: defaultTemplateData, loading} = useIndicoAxios(
    {url: defaultTemplate && getDefaultTemplateURL({template_name: defaultTemplate})},
    {manual: !defaultTemplate}
  );

  const createTemplate = async data => {
    try {
      const {data: template} = await indicoAxios.post(addTemplateURL(targetLocator), data);
      dispatch({type: 'ADD_TEMPLATE', template});
      // back to list of templates
      history.push(templateListURL(targetLocator));
    } catch ({
      response: {
        data: {webargs_errors: errors},
      },
    }) {
      return errors;
    }
  };

  return (
    <>
      <ManagementPageBackButton url={templateListURL(targetLocator)} />
      <TemplatePane
        onSubmit={createTemplate}
        targetLocator={targetLocator}
        template={defaultTemplateData || undefined}
        loading={loading}
        add
      />
    </>
  );
}

NewTemplatePane.propTypes = {
  dispatch: PropTypes.func.isRequired,
  targetLocator: targetLocatorSchema.isRequired,
  defaultTemplate: PropTypes.string,
};

NewTemplatePane.defaultProps = {
  defaultTemplate: '',
};

export default function TemplateManagement({initialState, defaultTemplates, targetLocator}) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const targetIdParams = Object.keys(targetLocator);

  // hide success messages after 2.5 seconds
  useEffect(() => {
    if (state.message) {
      setTimeout(() => dispatch({type: 'RESET_MESSAGE'}), 2500);
    }
  }, [state.message]);

  return (
    <>
      {state.message && (
        <Message success>
          <Message.Content>{state.message}</Message.Content>
        </Message>
      )}
      <Router>
        <Switch>
          <Route
            exact
            path={routerPathFromFlask(addTemplateURL, targetIdParams)}
            render={() => <NewTemplatePane dispatch={dispatch} targetLocator={targetLocator} />}
          />
          <Route
            exact
            path={routerPathFromFlask(addDefaultTemplateURL, [...targetIdParams, 'template_name'])}
            render={({
              match: {
                params: {template_name: templateName},
              },
            }) => (
              <NewTemplatePane
                dispatch={dispatch}
                targetLocator={targetLocator}
                defaultTemplate={templateName}
              />
            )}
          />
          <Route
            exact
            path={[routerPathFromFlask(templateURL, [...targetIdParams, 'template_id'])]}
            render={() => (
              <EditTemplatePane
                templates={state.ownTemplates}
                dispatch={dispatch}
                targetLocator={targetLocator}
              />
            )}
          />
          <Route
            exact
            path={routerPathFromFlask(templateListURL, targetIdParams)}
            render={() => (
              <TemplateListPane
                dispatch={dispatch}
                defaultTemplates={defaultTemplates}
                targetLocator={targetLocator}
                {...state}
              />
            )}
          />
        </Switch>
      </Router>
    </>
  );
}

TemplateManagement.propTypes = {
  initialState: PropTypes.shape({
    ownTemplates: PropTypes.arrayOf(templateSchema),
    inheritedTemplates: PropTypes.arrayOf(templateSchema),
  }).isRequired,
  defaultTemplates: PropTypes.objectOf(defaultTemplateSchema).isRequired,
  targetLocator: targetLocatorSchema.isRequired,
};
