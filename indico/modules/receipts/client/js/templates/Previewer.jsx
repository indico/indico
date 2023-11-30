// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {pdfjs, Document, Page} from 'react-pdf';
import {Loader, Message, Pagination} from 'semantic-ui-react';

import PlaceholderInfo from 'indico/react/components/PlaceholderInfo';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {makeAsyncDebounce} from 'indico/utils/debounce';

import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

import './Previewer.module.scss';

pdfjs.GlobalWorkerOptions.workerSrc = `/dist/js/pdf.worker-${pdfjs.version}.min.js`;

const MESSAGE_HEADERS = {
  yaml: Translate.string('YAML Metadata'),
  html: Translate.string('HTML Code'),
  css: Translate.string('CSS Stylesheet'),
  jinja: Translate.string('Jinja Template'),
  custom_fields: Translate.string('Template Parameters'),
};

const processPlaceholders = placeholderData =>
  Object.entries(placeholderData).map(([name, value]) =>
    _.isObject(value)
      ? {
          name: _.isArray(value) ? `${name}.0` : name,
          parametrized: true,
          params: Object.entries(_.isArray(value) ? value[0] : value).map(
            ([param, paramValue]) => ({
              param,
              description: JSON.stringify(paramValue),
            })
          ),
        }
      : {name, description: JSON.stringify(value)}
  );

const debounce = makeAsyncDebounce(250);

export default function Previewer({url, data}) {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [placeholders, setPlaceholders] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    (async () => {
      try {
        const {data: previewData} = await debounce(() => indicoAxios.post(url, data));
        const dummyData = previewData.data;
        const newContent = Uint8Array.from(atob(previewData.pdf), c => c.charCodeAt(0)).buffer;
        if (dummyData) {
          setPlaceholders(processPlaceholders(dummyData));
        }
        setLoading(false);
        setContent(newContent);
        setError(null);
      } catch (e) {
        const {
          response: {status, data: respData},
        } = e;
        if (status === 422) {
          if (respData.webargs_errors) {
            setError(respData.webargs_errors);
          } else {
            setError({jinja: [respData.error.message]});
          }
        } else {
          handleAxiosError(e);
        }
      }
    })();
  }, [url, data]);

  return (
    <>
      {placeholders && <PlaceholderInfo placeholders={placeholders} jinja />}
      {error &&
        Object.entries(error).map(([entry, errs]) => (
          <Message key={entry} error visible={!!error}>
            <Message.Header>{MESSAGE_HEADERS[entry]}</Message.Header>
            <ul>
              {errs.map(err => (
                <li key={err}>{err}</li>
              ))}
            </ul>
          </Message>
        ))}
      <div styleName={`previewer ${loading ? 'loading' : ''}`}>
        {content && (
          <Document
            file={content}
            loading={<Loader active />}
            onLoadSuccess={({numPages: n}) => {
              setNumPages(n);
              setPageNumber(1);
            }}
          >
            <Page pageNumber={pageNumber} />
          </Document>
        )}
        {numPages && (
          <Pagination
            disabled={numPages < 2}
            totalPages={numPages}
            boundaryRange={0}
            activePage={pageNumber}
            onPageChange={(__, {activePage}) => {
              setPageNumber(activePage);
            }}
            firstItem={null}
            lastItem={null}
            secondary
            styleName="pagination"
          />
        )}
      </div>
    </>
  );
}

Previewer.propTypes = {
  url: PropTypes.string.isRequired,
  data: PropTypes.object.isRequired,
};
