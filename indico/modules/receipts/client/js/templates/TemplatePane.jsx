// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import templateListURL from 'indico-url:receipts.template_list';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Link} from 'react-router-dom';
import {Form} from 'semantic-ui-react';

import {ManagementPageSubTitle} from 'indico/react/components';
import {FinalInput, FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {targetLocatorSchema, templateSchema} from './util';
import './TemplatePane.module.scss';

export default function TemplatePage({template, onSubmit, targetLocator}) {
  const initValues = template ? _.pick(template, ['title', 'html', 'css', 'yaml']) : {};

  return (
    <>
      <ManagementPageSubTitle title={Translate.string('Add Receipt / Certificate template')} />
      <FinalForm onSubmit={onSubmit} initialValues={initValues}>
        {fprops => (
          <Form onSubmit={fprops.handleSubmit}>
            <FinalInput
              name="title"
              label="Title"
              component={Form.Input}
              type="text"
              required
              rows={24}
            />
            <Form.Group widths="equal">
              <FinalTextArea
                name="html"
                label={Translate.string('HTML / Jinja')}
                type="text"
                required
                rows={24}
              />
              <div styleName="stacked-fields">
                <FinalTextArea name="css" label={Translate.string('CSS')} type="text" rows={10} />
                <FinalTextArea
                  name="yaml"
                  label={Translate.string('Metadata (YAML)')}
                  nullIfEmpty
                  type="text"
                  rows={10}
                />
              </div>
            </Form.Group>
            <Form.Group styleName="buttons">
              <FinalSubmitButton label={Translate.string('Submit')} />
              <Link to={templateListURL(targetLocator)} className="ui button">
                <Translate>Cancel</Translate>
              </Link>
            </Form.Group>
          </Form>
        )}
      </FinalForm>
    </>
  );
}

TemplatePage.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  template: templateSchema,
  targetLocator: targetLocatorSchema.isRequired,
};

TemplatePage.defaultProps = {
  template: null,
};
