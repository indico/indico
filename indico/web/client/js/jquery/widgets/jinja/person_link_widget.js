// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global showFormErrors:false strnatcmp:false */

import _ from 'lodash';
import React, {useState} from 'react';
import ReactDOM from 'react-dom';

import {UserSearch} from 'indico/react/components/principals/Search';
import {useFavoriteUsers} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {$T} from 'indico/utils/i18n';

(function(global) {
  global.setupPersonLinkWidget = function setupPersonLinkWidget(options) {
    options = $.extend(
      true,
      {
        fieldId: null,
        disableUserSearch: false,
        eventId: null,
        authorTypes: null,
        showEmptyCoauthors: true,
        sort: true,
        sortByLastName: false,
        sessionUser: null,
        allow: {
          authors: false,
          submitters: false,
          emptyEmail: false,
          externalUsers: true,
          speakers: true,
        },
        defaults: {
          authorType: 0,
          isSpeaker: false,
          isSubmitter: false,
        },
        require: {
          primaryAuthor: false,
          secondaryAuthor: false,
          submitter: false,
          speaker: false,
        },
      },
      options
    );

    const $field = $(`#${options.fieldId}`);
    const $fieldDisplay = $(`#people-list-${options.fieldId}`);
    const $authorList = $fieldDisplay.find(`#author-list-${options.fieldId}`);
    const $noAuthorPlaceholder = $fieldDisplay.find(`#no-author-placeholder-${options.fieldId}`);
    const $coauthorList = $fieldDisplay.find(`#coauthor-list-${options.fieldId}`);
    const $coauthorListTitle = $fieldDisplay.find(`#coauthor-list-title-${options.fieldId}`);
    const $noCoauthorPlaceholder = $fieldDisplay.find(
      `#no-coauthor-placeholder-${options.fieldId}`
    );
    const $otherList = $fieldDisplay.find(`#other-list-${options.fieldId}`);
    const $otherListTitle = $fieldDisplay.find(`#other-list-title-${options.fieldId}`);
    const $noOtherPlaceholder = $fieldDisplay.find(`#no-other-placeholder-${options.fieldId}`);
    const $buttonAddNew = $(`#add-new-${options.fieldId}`);
    const $buttonAddMyself = $(`#add-myself-${options.fieldId}`);
    const $buttonAlphaOrder = $fieldDisplay.find('.alpha-order-switch');
    const $form = $field.closest('form');
    let customOrder = !$buttonAlphaOrder.hasClass('active');
    let maxNewPersonID = 0;

    let forceUpdateUserSearch = () => {};

    function setNewPersonID(person) {
      person.id = `new-${maxNewPersonID}`;
      maxNewPersonID++;
    }

    function updatePersonOrder() {
      const people = _.map($fieldDisplay.find('.person-row'), function(e) {
        return $(e).data('person');
      });
      people.forEach(function(person, i) {
        person.displayOrder = customOrder ? i + 1 : 0;
        $field.principalfield('set', person.id, {displayOrder: person.displayOrder});
      });
    }

    function setupList(entryType, $list, sortedPeople) {
      const isSortable = options.sort === true;

      $list.empty();

      if (isSortable) {
        $list.sortable({
          axis: 'y',
          containment: 'parent',
          cursor: 'move',
          distance: 10,
          handle: '.sort-handle',
          items: '> .person-row',
          tolerance: 'pointer',
          forceHelperSize: true,
          forcePlaceholderSize: true,
          helper(e, item) {
            const originals = item.children();
            const helper = item.clone();
            helper.children().each(function(i) {
              $(this).width(originals.eq(i).width());
            });
            return helper;
          },
          update: updatePersonOrder,
        });
      }

      sortedPeople.forEach(function(person) {
        renderPerson(person, $list, entryType, isSortable && customOrder);
      });
    }

    function getName(person) {
      return options.sortByLastName
        ? '{0}, {1}'.format(person.familyName, person.firstName)
        : person.name;
    }

    function renderPeople(people) {
      $coauthorList.empty();
      $otherList.empty();

      const sortedPeople = _.clone(people);
      sortedPeople.sort(function(person1, person2) {
        const k1 = `${person1.displayOrder} ${getName(person1)}`;
        const k2 = `${person2.displayOrder} ${getName(person2)}`;
        return strnatcmp(k1, k2);
      });

      // Set default values
      people.forEach(function(person) {
        setPersonDefaults(person);
      });

      if (options.authorTypes) {
        const sortedAuthors = _.filter(sortedPeople, function(person) {
          return person.authorType === options.authorTypes.primary;
        });
        const sortedCoAuthors = _.filter(sortedPeople, function(person) {
          return person.authorType === options.authorTypes.secondary;
        });
        const sortedOthers = _.filter(sortedPeople, function(person) {
          return (
            !options.authorTypes ||
            person.authorType === options.authorTypes.none ||
            (!options.allow.authors && person.isSpeaker)
          );
        });
        setupList(options.authorTypes.primary, $authorList, sortedAuthors);
        setupList(options.authorTypes.secondary, $coauthorList, sortedCoAuthors);
        setupList(options.authorTypes.none, $otherList, sortedOthers);
      } else {
        setupList(null, $otherList, sortedPeople);
      }

      $noAuthorPlaceholder.toggle($authorList.is(':empty'));
      if (!options.showEmptyCoauthors) {
        $coauthorListTitle.toggle($coauthorList.is(':not(:empty)'));
      } else {
        $noCoauthorPlaceholder.toggle($coauthorList.is(':empty'));
      }
      $otherListTitle.toggle($otherList.is(':not(:empty)'));
      $noOtherPlaceholder.toggle($otherList.is(':empty'));
    }

    function renderPerson(person, $list, entryType, isSortable) {
      const $speakerLabel = $('<span>')
        .addClass('i-label small speaker')
        .text($T.gettext('Speaker'));
      const $personRow = $('<div>')
        .addClass('person-row')
        .data('person', person);
      const $personName = $('<div>')
        .addClass('name')
        .text(getName(person));
      const $personRoles = $('<span>').addClass('person-roles');
      const $personButtons = $('<span>').addClass('person-buttons');
      const $buttonRemove = $('<a>')
        .addClass('i-link danger icon-close')
        .attr('title', $T.gettext('Remove person'));
      const $buttonEdit = $('<a>')
        .addClass('i-link icon-edit')
        .attr('title', $T.gettext('Edit information'));
      const $buttonConfig = $('<a>')
        .addClass('i-link icon-settings')
        .attr('title', $T.gettext('Configure roles'));

      $personRow
        .append($personName)
        .append($personRoles)
        .append($personButtons);
      $personButtons.append($buttonRemove).append($buttonEdit);

      if (isSortable) {
        $personRow.prepend('<span class="sort-handle">');
      }

      if (options.allow.submitters) {
        const $submitterLabel = $('<span>')
          .addClass('i-label small submitter')
          .text($T.gettext('Submitter'));
        $personRoles.append($submitterLabel.toggleClass('selected', person.isSubmitter));
      }

      if (options.allow.authors && options.allow.speakers) {
        $personRoles.prepend($speakerLabel.toggleClass('selected', person.isSpeaker));
      }

      if (entryType !== null && entryType === options.authorTypes.none) {
        if (options.allow.authors && options.allow.speakers) {
          $speakerLabel.addClass('other');
        }
      }

      $list.append($personRow);

      if (options.allow.submitters || options.allow.authors) {
        $personButtons.append($buttonConfig);
        setupPersonConfig(person, $buttonConfig, $personRow, $personRoles);
      }
      $buttonEdit.on('click', function() {
        $field.principalfield('edit', person.id);
      });
      $buttonRemove.on('click', function() {
        $field.principalfield('removeOne', person.id);
        forceUpdateUserSearch();
      });
    }

    function setPersonDefaults(person) {
      if (person.authorType === undefined) {
        person.authorType = options.defaults.authorType;
      }
      if (person.isSpeaker === undefined) {
        person.isSpeaker = options.defaults.isSpeaker;
      }
      if (person.isSubmitter === undefined) {
        person.isSubmitter = options.defaults.isSubmitter;
      }
      if (person.id === undefined) {
        setNewPersonID(person);
      }
    }

    function setupPersonConfig(person, $element, $personRow, $personRoles) {
      const $buttons = $('<div>');
      const $buttonsSeparator = $('<div>')
        .addClass('titled-rule')
        .text($T.gettext('or'));
      const $submitterLabel = $personRoles.find('.submitter');
      const $speakerLabel = $personRoles.find('.speaker');

      function actionButton(moveText, $targetList, targetData) {
        const $button = $('<div>')
          .addClass('action-row')
          .text(moveText);
        return $button.on('click', function() {
          $element.qbubble('hide');
          if ($targetList) {
            $personRow.appendTo($targetList);
            updatePersonOrder();
          }
          $field.principalfield('set', person.id, targetData);
        });
      }

      if (options.allow.authors) {
        if (person.authorType !== options.authorTypes.primary) {
          $buttons.append(
            actionButton($T.gettext('Move to authors'), $authorList, {authorType: 1})
          );
        }

        if (person.authorType !== options.authorTypes.secondary) {
          $buttons.append(
            actionButton($T.gettext('Move to co-authors'), $coauthorList, {authorType: 2})
          );
        }

        if (options.allow.speakers) {
          if (person.authorType !== options.authorTypes.none) {
            $buttons.append(
              actionButton($T.gettext('Move to others'), $otherList, {
                authorType: 0,
                isSpeaker: true,
              })
            );
            const text = person.isSpeaker
              ? $T.gettext('Not a speaker anymore')
              : $T.gettext('Make a speaker');

            $buttons.append($buttonsSeparator);
            $buttons.append(actionButton(text, null, {isSpeaker: !person.isSpeaker}));

            $speakerLabel.on('click', function() {
              $field.principalfield('set', person.id, {isSpeaker: !person.isSpeaker});
            });
          } else {
            $speakerLabel.qtip({
              content: {
                text: $T.gettext(
                  "People in the 'Others' section <strong>must</strong> be speakers."
                ),
              },
              show: {
                event: 'click',
                solo: true,
              },
              hide: {
                event: 'unfocus click',
              },
            });
          }
        }
      }

      if (options.allow.submitters) {
        const $submitterButton = $('<div>').addClass('action-row');
        $submitterButton.text(
          person.isSubmitter
            ? $T.gettext('Revoke submission rights')
            : $T.gettext('Grant submission rights')
        );
        $submitterButton.on('click', function() {
          $element.qbubble('hide');
          $field.principalfield('set', person.id, {isSubmitter: !person.isSubmitter});
        });
        $buttons.append($submitterButton);
        $submitterLabel.on('click', function() {
          $field.principalfield('set', person.id, {isSubmitter: !person.isSubmitter});
        });
      }

      $element.qbubble({
        style: {
          classes: 'person-link-qbubble',
        },
        content: {
          text: $buttons,
        },
        position: {
          my: 'left middle',
          at: 'right middle',
          adjust: {x: 15},
        },
        events: {
          show() {
            $element.addClass('active');
            $element.closest('.person-row').addClass('active');
          },
          hide() {
            $element.removeClass('active');
            $element.closest('.person-row').removeClass('active');
          },
        },
      });
    }

    $field.principalfield({
      eventId: options.eventId,
      allowExternalUsers: options.allow.externalUsers,
      allowEmptyEmail: options.allow.emptyEmail,
      multiChoice: true,
      overwriteChoice: false,
      render: renderPeople,
      onAdd(people) {
        people.forEach(function(person) {
          if (person.authorType === undefined) {
            const maxOrder = _.max(people, _.iteratee('displayOrder')).displayOrder || 0;
            setPersonDefaults(person);
            person.displayOrder = customOrder ? maxOrder + 1 : 0;
          }
        });
      },
    });

    $buttonAddNew.on('click', function() {
      $field.principalfield('enter');
    });

    $buttonAddMyself.on('click', function() {
      $field.principalfield('add', [options.sessionUser]);
      forceUpdateUserSearch();
    });

    function getSortingMessage() {
      if (customOrder) {
        return $T.gettext('Custom sorting has been applied. Click to restore alphabetical order.');
      } else {
        return $T.gettext('Alphabetical sorting is ON. Click to turn it off.');
      }
    }

    $buttonAlphaOrder.qtip({content: getSortingMessage});
    $buttonAlphaOrder.on('click', function() {
      const $list = $fieldDisplay.find('.person-list');
      customOrder = !customOrder;
      $buttonAlphaOrder.toggleClass('active', !customOrder);
      if (customOrder) {
        updatePersonOrder();
      } else {
        $list.find('.person-row').each(function() {
          $(this).data('person').displayOrder = 0;
        });
      }
      $field.principalfield('refresh');
    });

    $form.on('submit', function(evt) {
      const e = $.Event('ajaxForm:validateBeforeSubmit');
      $(this).trigger(e);
      if (e.isDefaultPrevented()) {
        evt.preventDefault();
      }
    });

    $field.closest('form').on('ajaxForm:validateBeforeSubmit', function(evt) {
      const $this = $(this);
      const req = options.require;

      if (
        req.primaryAuthor ||
        req.secondaryAuthor ||
        req.submitter ||
        req.speaker ||
        !options.allow.speakers
      ) {
        const $formField = $field.closest('.form-field');
        const $formGroup = $field.closest('.form-group');
        const hiddenData = JSON.parse($field.val());
        let hasError = false;

        if (req.speaker && !hiddenData.some(x => x.isSpeaker)) {
          hasError = true;
          $formField.data('error', $T.gettext('You must add at least one speaker'));
        } else if (req.submitter && !hiddenData.some(x => x.isSubmitter)) {
          hasError = true;
          $formField.data('error', $T.gettext('You must add at least one submitter'));
        } else if (req.secondaryAuthor && !hiddenData.some(x => x.authorType === 2)) {
          hasError = true;
          $formField.data('error', $T.gettext('You must add at least one co-author'));
        } else if (req.primaryAuthor && !hiddenData.some(x => x.authorType === 1)) {
          hasError = true;
          $formField.data('error', $T.gettext('You must add at least one author'));
        } else if (!options.allow.speakers && hiddenData.some(x => x.authorType === 0)) {
          hasError = true;
          $formField.data(
            'error',
            $T.gettext(
              'You cannot have users in the Other section, please make ' +
                'them authors or co-authors'
            )
          );
        }

        if (hasError) {
          evt.preventDefault();
          $formGroup.addClass('has-error');
          showFormErrors($this.parent());
        } else {
          $formGroup.removeClass('has-error');
          $formField.removeData('error');
        }
      }
    });

    const getExistingUsers = () =>
      _.map($fieldDisplay.find('.person-row'), function(e) {
        const person = $(e).data('person');
        if (person._type === undefined) {
          // new entry not linked to anyone
          return null;
        } else if (person._type === 'PersonLink') {
          return `User:${person.userId}`;
        } else if (person._type === 'Avatar') {
          // newly added users from search only have a `new-n` ID but we can use their identifier
          return person.identifier || `User:${person.id}`;
        } else {
          console.error(`Invalid person type ${person._type}: ${person}`);
          return null;
        }
      }).filter(id => id !== null);

    const searchTrigger = triggerProps => (
      <span className="i-button highlight" type="button" {...triggerProps}>
        <Translate>Search</Translate>
      </span>
    );

    const getLegacyType = identifier => {
      if (identifier.startsWith('User:')) {
        return 'Avatar';
      } else if (identifier.startsWith('EventPerson:')) {
        return 'EventPerson';
      } else {
        // likely ExternalUser; we have no type - see the `get_event_person` python util
        return null;
      }
    };

    const UserSearchWrapper = () => {
      const [favoriteUsers] = useFavoriteUsers();
      // This is super ugly, but we need to trigger a re-render from outside the
      // react code to use the new existingUsers list
      const [, _setState] = useState();
      forceUpdateUserSearch = () => _setState({});

      return (
        <UserSearch
          favorites={favoriteUsers}
          existing={getExistingUsers()}
          onAddItems={people => {
            $field.principalfield(
              'add',
              people.map(({identifier, id, name, firstName, lastName, email, affiliation}) => ({
                identifier,
                name,
                id,
                familyName: lastName,
                firstName,
                email,
                affiliation,
                _type: getLegacyType(identifier),
              }))
            );
            forceUpdateUserSearch();
          }}
          withExternalUsers={options.allow.externalUsers}
          triggerFactory={searchTrigger}
          withEventPersons={options.eventId !== null}
          eventId={options.eventId}
        />
      );
    };

    if (!options.disableUserSearch) {
      ReactDOM.render(
        <UserSearchWrapper />,
        document.getElementById(`principalField-${options.fieldId}`)
      );
    }
  };
})(window);
