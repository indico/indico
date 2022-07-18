// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {pdfjs, Document, Page} from 'react-pdf';
import {Loader, Pagination} from 'semantic-ui-react';

import './TemplatePane.module.scss';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

const debouncedRequest = _.throttle(
  (setContent, url, data) =>
    (async () => {
      try {
        const {data: content} = await indicoAxios.post(url, data, {responseType: 'arraybuffer'});
        setContent(content);
      } catch (error) {
        handleAxiosError(error);
        return;
      }
    })(),
  4000
);

export default function Previewer({url, data}) {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);

  useEffect(() => {
    setLoading(true);
    debouncedRequest(
      c => {
        setLoading(false);
        setContent(c);
      },
      url,
      data
    );
  }, [url, data]);

  return (
    <div styleName={loading ? 'loading' : null}>
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
    </div>
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
