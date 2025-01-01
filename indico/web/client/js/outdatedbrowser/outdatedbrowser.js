// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import UserAgentParser from 'ua-parser-js';

// Based on https://github.com/mikemaccana/outdated-browser-rework (MIT-licensed)

function parseMajorVersion(version) {
  return version.replace(/[^\d.]/g, '').split('.')[0];
}

function parseMinorVersion(version) {
  return version.replace(/[^\d.]/g, '').split('.')[1];
}

export default function outdatedBrowser({browserSupport, messages}) {
  const main = () => {
    if (document.cookie.indexOf('outdatedbrowser=hide') !== -1) {
      return;
    }

    const parsedUserAgent = new UserAgentParser(window.navigator.userAgent).getResult();
    const outdatedUI = document.getElementById('outdated-browser');

    let browserName = parsedUserAgent.browser.name;
    let browserMajorVersion = +parsedUserAgent.browser.major;
    let browserMinorVersion = +parseMinorVersion(parsedUserAgent.browser.version) || 0;

    // Determines where we tell users to go for upgrades.
    let updateSource = 'web';
    if (parsedUserAgent.os.name === 'Android') {
      updateSource = 'googlePlay';
    }
    if (parsedUserAgent.os.name === 'iOS') {
      updateSource = 'appStore';
      // browserslist goes by iOS version since everything there uses the safari rendering
      // engine and it's tied to the OS version
      browserMajorVersion = +parseMajorVersion(parsedUserAgent.os.version);
      browserMinorVersion = +parseMinorVersion(parsedUserAgent.os.version);
      // Every browser on iOS uses webkit, so we pretend it's mobile safari
      browserName = 'Mobile Safari';
    }

    let done = true;

    const changeOpacity = opacityValue => {
      outdatedUI.style.opacity = opacityValue / 100;
      outdatedUI.style.filter = `alpha(opacity=${opacityValue})`;
    };

    const fadeIn = opacityValue => {
      changeOpacity(opacityValue);
      if (opacityValue === 1) {
        outdatedUI.style.display = 'table';
      }
      if (opacityValue === 100) {
        done = true;
      }
    };

    const isBrowserUnsupported = () => {
      return browserSupport[browserName] === false;
    };

    const isBrowserOutOfDate = () => {
      let isOutOfDate = false;
      if (isBrowserUnsupported()) {
        isOutOfDate = true;
      } else if (browserName in browserSupport) {
        const minVersion = browserSupport[browserName];
        if (typeof minVersion === 'object') {
          const minMajorVersion = minVersion.major;
          const minMinorVersion = minVersion.minor;

          if (browserMajorVersion < minMajorVersion) {
            isOutOfDate = true;
          } else if (browserMajorVersion === minMajorVersion) {
            if (browserMinorVersion < minMinorVersion) {
              isOutOfDate = true;
            }
          }
        } else if (browserMajorVersion < minVersion) {
          isOutOfDate = true;
        }
      }
      return isOutOfDate;
    };

    const makeFadeInFunction = opacityValue => () => {
      fadeIn(opacityValue);
    };

    const getMessageContent = () => {
      const unsupported = isBrowserUnsupported();
      let browserSupportMessage, updateMessages;
      if (unsupported) {
        browserSupportMessage = messages.unsupported;
        updateMessages = messages.updateUnsupported;
      } else {
        browserSupportMessage = messages.outdated;
        updateMessages = messages.updateOutdated;
      }

      const updateMessage = updateMessages[updateSource];
      return `
        <div class="vertical-center">
          <h6>
            ${browserSupportMessage}
          </h6>
          <p>${updateMessage}</p>
          <p class="last">
            <a href="#" id="close-outdated-browser" title="Close">&times;</a>
          </p>
        </div>
      `;
    };

    // Check if browser is supported
    if (isBrowserOutOfDate()) {
      // This is an outdated browser
      if (done && outdatedUI.style.opacity !== '1') {
        done = false;

        for (let opacity = 1; opacity <= 100; opacity++) {
          setTimeout(makeFadeInFunction(opacity), opacity * 8);
        }
      }

      const insertContentHere = document.getElementById('outdated-browser');
      insertContentHere.innerHTML = getMessageContent();
      const buttonClose = document.getElementById('close-outdated-browser');
      buttonClose.onmousedown = () => {
        outdatedUI.style.display = 'none';
        const duration = 86400;
        const expiry = new Date(new Date().getTime() + duration * 1000).toGMTString();
        document.cookie = `outdatedbrowser=hide; expires=${expiry}; path=/`;
        return false;
      };
    }
  };

  // Load main when DOM ready.
  const oldOnload = window.onload;
  if (typeof window.onload !== 'function') {
    window.onload = main;
  } else {
    window.onload = () => {
      if (oldOnload) {
        oldOnload();
      }
      main();
    };
  }
}
