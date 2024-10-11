// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/**
 * Handle a situation where a container loses focus
 *
 * The container is an element such as a dialog or a list. We cannot
 * simply use 'blur' or 'focusout' in this case, because moving from
 * one element to another triggers a series of focusout/blur and
 * focusin/focus events. Another issue is related to the Safari browser
 * which will not focus buttons when clicked. For instance, clicking a
 * button within a container might behave as if the user has unfocused
 * a descendant and focused the document itself.
 *
 * This function abstracts over the setup of the necessary event
 * listeners to handle focus loss in a more user-friendly manner.
 *
 * The supplied callback function is called whenever focus is lost.
 * It receives no arguments, and its return value is ignored.
 *
 * The return value of this function is a function that will remove
 * the event listeners.
 */
export function focusLost(container, callback) {
  const abortListeners = new AbortController();

  // Marker that tells the listeners to temporarily ignore events. This
  // is a workaround for the Safari behavior where clicks on buttons causes
  // the browser to behave as if the focus has shifted from the previously
  // focused element to the document itself (rather than the button).
  let noImmediateClose = false;

  container.addEventListener(
    'pointerdown',
    () => {
      // When user clicks within the container, we set a marker that temporarily
      // disables the
      // Because Safari does not focus buttons (and other elements) when they
      // are clicked, we need to mark the dialog as having received such clicks
      // and test for it in the close handler.
      noImmediateClose = true;
      setTimeout(() => {
        // Unset with a delay to allow focusout handler to see this flag.
        // It must still be unset so it doesn't linger on forever. The delay
        // was chosen based on trial and error. In general, you don't want
        // to make it shorter, but you may increase it if some browser/OS
        // combination unsets the flag too quickly.
        noImmediateClose = false;
      }, 100);
    },
    {signal: abortListeners.signal}
  );
  container.addEventListener(
    'focusout',
    () => {
      // When a button (or anything) in the container is clicked,
      // `noImmediateClose`. When that's the case, we don't need to do
      // anything.
      if (noImmediateClose) {
        return;
      }

      // The focusout event is triggered on the dialog or somewhere in it.
      // We use requestAnimationFrame to allow the target element to get
      // focused in order to find out whether the focus is still within the
      // container.
      requestAnimationFrame(() => {
        // If the newly-focused element is outside the container, it lost focus.
        if (!container.contains(document.activeElement)) {
          callback();
        }
      });
    },
    {signal: abortListeners.signal}
  );

  return () => abortListeners.abort();
}
