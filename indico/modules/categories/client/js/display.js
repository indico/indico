// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {domReady} from 'indico/utils/domstate';
import {$T} from 'indico/utils/i18n';
import 'indico/custom_elements/ind_with_tooltip';
import 'indico/custom_elements/ind_with_toggletip';

const delayedMessageDelay = 1000;
const messageClearDelay = 10000;
const saveStateDelay = 500;

const getCsrfToken = () => document.getElementById('csrf-token').getAttribute('content');

customElements.define(
  'ind-category-list',
  class extends HTMLElement {
    connectedCallback() {
      domReady.then(() => {
        const url = this.getAttribute('subcat-info-url');
        if (!url) {
          return;
        }
        fetch(url)
          .then(res => res.json())
          .then(data => {
            for (const id in data.event_counts) {
              const count = data.event_counts[id];
              this.querySelector(`#category-${id} .event-count`).textContent = count.value
                ? $T.ngettext('{0} event', '{0} events', count.value).format(count.pretty)
                : $T.gettext('no events');
            }
          });
      });
    }
  }
);

customElements.define(
  'ind-hidden-event-trigger',
  class extends HTMLElement {
    connectedCallback() {
      const listName = this.getAttribute('list-name');
      const url = this.getAttribute('url');

      domReady.then(() => {
        const showTrigger = this.querySelector('[value="show"]');
        const hideTrigger = this.querySelector('[value="hide"]');
        const message = this.querySelector('[aria-live]');

        const saveDefaultState = () => {
          clearTimeout(this.debounceTimer);
          this.debounceTimer = setTimeout(() => {
            fetch(url, {
              method: this.getAttribute('shown') === 'true' ? 'PUT' : 'DELETE',
              headers: {
                'X-CSRF-Token': getCsrfToken(),
              },
            });
          }, saveStateDelay);
        };

        const clearMessage = () => {
          clearTimeout(message.timeout);
          message.textContent = '';
        };

        const setAutoexpiringMessage = messageKey => {
          clearTimeout(message.timeout);
          message.textContent = message.dataset[messageKey];
          message.timeout = setTimeout(clearMessage, messageClearDelay);
        };

        const setDelayedMessage = messageKey => {
          clearTimeout(message.timeout);
          message.timeout = setTimeout(() => {
            setAutoexpiringMessage(messageKey);
          }, delayedMessageDelay);
        };

        window.addEventListener(`shownHiddenEvents_${listName}`, () => {
          this.setAttribute('shown', true);
          setAutoexpiringMessage('loadedMessage');
        });

        window.addEventListener(`failedLoadingHiddenEvents_${listName}`, () => {
          setAutoexpiringMessage('errorMessage');
        });

        hideTrigger.addEventListener('click', () => {
          clearMessage();
          this.setAttribute('shown', false);
          window.dispatchEvent(new Event(`hideHiddenEvents_${listName}`));
          saveDefaultState();
        });

        const showHiddenEvents = () => {
          setDelayedMessage('loadingMessage');
          window.dispatchEvent(new Event(`loadHiddenEvents_${listName}`));
        };

        showTrigger.addEventListener('click', () => {
          showHiddenEvents();
          saveDefaultState();
        });

        if (this.getAttribute('shown') === 'true') {
          requestIdleCallback(showHiddenEvents); // XXX: Delay invoking this callback so that the target listener is registetred
        }
      });
    }
  }
);

customElements.define(
  'ind-hidden-event-list',
  class extends HTMLElement {
    connectedCallback() {
      const listName = this.getAttribute('list-name');
      const url = new URL(this.getAttribute('url'), window.location);
      let listLoaded;

      Object.entries(JSON.stringify(this.getAttribute('extra-params'))).forEach(([k, v]) =>
        url.searchParams.set(k, v)
      );
      url.searchParams.set('after', this.getAttribute('after'));
      url.searchParams.set('before', this.getAttribute('before'));
      if (this.getAttribute('flat') === 'true') {
        url.searchParams.set('flat', 1);
      }

      domReady.then(() => {
        window.addEventListener(`loadHiddenEvents_${listName}`, () => {
          if (!listLoaded) {
            listLoaded = fetch(url)
              .then(res => res.json())
              .then(data => (this.innerHTML = data.html))
              .then(() => true)
              .catch(() => {
                window.dispatchEvent(new Event(`failedLoadingHiddenEvents_${listName}`));
              });
          }
          listLoaded.then(isLoaded => {
            if (isLoaded) {
              this.hidden = false;
              window.dispatchEvent(new Event(`shownHiddenEvents_${listName}`));
            } else {
              listLoaded = undefined; // XXX: Unset the reference so we can retry again later
            }
          });
        });
        window.addEventListener(`hideHiddenEvents_${listName}`, () => {
          this.hidden = true;
        });
      });
    }
  }
);

const IMAGE = 1;
const AUDIO = 2;
const VIDEO = 3;
const TEXT = 4;
const PREVIEW_TYPES = {
  'audio/mpeg': AUDIO,
  'audio/ogg': AUDIO,
  'audio/wav': AUDIO,
  'audio/webm': AUDIO,
  'image/bmp': IMAGE,
  'image/gif': IMAGE,
  'image/jpeg': IMAGE,
  'image/png': IMAGE,
  'image/tiff': IMAGE,
  'image/webp': IMAGE,
  'text/csv': TEXT,
  'text/plain': TEXT,
  'text/tab-separated-values': TEXT,
  'video/3g2': VIDEO,
  'video/3gp': VIDEO,
  'video/mp4': VIDEO,
  'video/mpeg': VIDEO,
  'video/webm': VIDEO,
  'video/x-msvideo': VIDEO,
};

customElements.define(
  'ind-attachment',
  class extends HTMLElement {
    connectedCallback() {
      domReady.then(() => {
        const attachmentLink = this.firstElementChild;
        const url = attachmentLink.href;
        const filename = attachmentLink.dataset.filename;
        const previewType = PREVIEW_TYPES[attachmentLink.dataset.contentType];

        if (previewType) {
          const previewDetails = {url, previewType, filename};
          attachmentLink.addEventListener('click', evt => {
            evt.preventDefault();
            window.dispatchEvent(new CustomEvent('previewAttachment', {detail: previewDetails}));
          });
        }
      });
    }
  }
);

customElements.define(
  'ind-attachment-preview-modal',
  class extends HTMLElement {
    connectedCallback() {
      domReady.then(() => {
        const dialog = this.querySelector('dialog');
        const previewContent = this.querySelector('article');
        const downloadLink = this.querySelector('a');
        const title = this.querySelector('.titlebar :first-child');
        const imageTemplate = this.querySelector('[data-type=image]').content;
        const audioTemplate = this.querySelector('[data-type=audio]').content;
        const videoTemplate = this.querySelector('[data-type=video]').content;
        const textTemplate = this.querySelector('[data-type=text]').content;
        const invalidTypeTemplate = this.querySelector('[data-type="invalid"]').content;

        dialog.addEventListener('close', () => {
          // XXX: Empty the contents so that any playback is stopped
          previewContent.replaceChildren();
        });

        dialog.addEventListener('click', evt => {
          if (evt.target.closest('button[value=close]') || evt.target === dialog) {
            dialog.close();
            dialog.dispatchEvent(new Event('close'));
          }
        });

        window.addEventListener('previewAttachment', evt => {
          const {url, previewType, filename} = evt.detail;
          let preview;

          downloadLink.href = url;
          title.textContent = $T.gettext('Previewing {0}').format(filename);

          switch (previewType) {
            case IMAGE:
              preview = imageTemplate.cloneNode(true).firstElementChild;
              preview.src = url;
              break;
            case AUDIO:
              preview = audioTemplate.cloneNode(true).firstElementChild;
              preview.querySelector('source').src = url;
              break;
            case VIDEO:
              preview = videoTemplate.cloneNode(true).firstElementChild;
              preview.querySelector('source').src = url;
              break;
            case TEXT: {
              preview = textTemplate.cloneNode(true).firstElementChild;
              const loadIndicatorDelay = 1000;
              const loading = preview.querySelector('span:first-of-type');
              const error = preview.querySelector('span:nth-of-type(2)');
              const content = preview.querySelector('pre');
              const loadingTimer = setTimeout(() => {
                loading.hidden = false;
              }, loadIndicatorDelay);
              fetch(url)
                .then(res => {
                  clearTimeout(loadingTimer);
                  loading.hidden = true;
                  if (!res.ok) {
                    throw Error('no content');
                  }
                  return res.text();
                })
                .then(text => {
                  content.textContent = text;
                  content.hidden = false;
                })
                .catch(() => {
                  error.hidden = false;
                });
              break;
            }
            default:
              preview = invalidTypeTemplate.cloneNode(true);
          }

          previewContent.append(preview);
          dialog.showModal();
        });
      });
    }
  }
);
