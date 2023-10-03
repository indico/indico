// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {pdfjs, Document, Page} from 'react-pdf';
import {Loader, Message, Pagination} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {makeAsyncDebounce} from 'indico/utils/debounce';

import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

import './Previewer.module.scss';

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

const MESSAGE_HEADERS = {
  yaml: Translate.string('YAML Metadata'),
  html: Translate.string('HTML Code'),
  css: Translate.string('CSS Stylesheet'),
  jinja: Translate.string('Jinja Template'),
};

const debounce = makeAsyncDebounce(250);

export default function Previewer({url, data}) {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    (async () => {
      try {
        setError(null);
        const {data: newContent} = await debounce(() =>
          indicoAxios.post(url, data, {responseType: 'arraybuffer'})
        );
        setLoading(false);
        setContent(newContent);
      } catch (e) {
        const {
          response: {status, data},
        } = e;
        if (status === 422) {
          const decoder = new TextDecoder('utf-8');
          const json = JSON.parse(decoder.decode(data));
          if (json.webargs_errors) {
            setError(json.webargs_errors);
          } else {
            setError({jinja: [json.error.message]});
          }
        } else {
          handleAxiosError(e);
        }
        return;
      }
    })();
  }, [url, data]);

  return (
    <>
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
  data: PropTypes.shape({
    title: PropTypes.string,
    html: PropTypes.string,
    css: PropTypes.string,
    yaml: PropTypes.string,
  }).isRequired,
};
