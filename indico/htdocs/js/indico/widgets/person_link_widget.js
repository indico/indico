/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

/* global showFormErrors:false strnatcmp:false */

(function(global) {
    'use strict';

    global.setupPersonLinkWidget = function setupPersonLinkWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            eventId: null,
            authorTypes: null,
            showEmptyCoauthors: true,
            sort: true,
            allow: {
                authors: false,
                submitters: false,
                emptyEmail: false,
                externalUsers: true,
                speakers: true
            },
            defaults: {
                authorType: 0,
                isSpeaker: false,
                isSubmitter: false
            },
            require: {
                primaryAuthor: false,
                secondaryAuthor: false,
                submitter: false,
                speaker: false
            }
        }, options);

        var $field = $('#' + options.fieldId);
        var $fieldDisplay = $('#people-list-' + options.fieldId);
        var $authorList = $fieldDisplay.find('#author-list-' + options.fieldId);
        var $noAuthorPlaceholder = $fieldDisplay.find('#no-author-placeholder-' + options.fieldId);
        var $coauthorList = $fieldDisplay.find('#coauthor-list-' + options.fieldId);
        var $coauthorListTitle = $fieldDisplay.find('#coauthor-list-title-' + options.fieldId);
        var $noCoauthorPlaceholder = $fieldDisplay.find('#no-coauthor-placeholder-' + options.fieldId);
        var $otherList = $fieldDisplay.find('#other-list-' + options.fieldId);
        var $otherListTitle = $fieldDisplay.find('#other-list-title-' + options.fieldId);
        var $noOtherPlaceholder = $fieldDisplay.find('#no-other-placeholder-' + options.fieldId);
        var $buttonAddExisting = $('#add-existing-' + options.fieldId);
        var $buttonAddNew = $('#add-new-' + options.fieldId);
        var $buttonAlphaOrder = $fieldDisplay.find('.alpha-order-switch');
        var $form = $field.closest('form');
        var customOrder = !$buttonAlphaOrder.hasClass('active');
        var maxNewPersonID = 0;

        function setNewPersonID(person) {
            person.id = 'new-' + maxNewPersonID;
            maxNewPersonID++;
        }

        function updatePersonOrder() {
            var people = _.map($fieldDisplay.find('.person-row'), function(e) {
                return $(e).data('person');
            });
            people.forEach(function(person, i) {
                person.displayOrder = customOrder ? (i + 1) : 0;
                $field.principalfield('set', person.id, {displayOrder: person.displayOrder});
            });
        }

        function setupList(entryType, $list, sortedPeople) {
            var isSortable = options.sort === true;

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
                    helper: function(e, item) {
                        var originals = item.children();
                        var helper = item.clone();
                        helper.children().each(function(i) {
                            $(this).width(originals.eq(i).width());
                        });
                        return helper;
                    },
                    update: updatePersonOrder
                });
            }

            sortedPeople.forEach(function(person) {
                renderPerson(person, $list, entryType, isSortable && customOrder);
            });
        }

        function renderPeople(people) {
            $coauthorList.empty();
            $otherList.empty();

            var sortedPeople = _.clone(people);
            sortedPeople.sort(function(person1, person2) {
                var k1 = person1.displayOrder + ' ' + person1.name;
                var k2 = person2.displayOrder + ' ' + person2.name;
                return strnatcmp(k1, k2);
            });

            // Set default values
            people.forEach(function(person) {
                setPersonDefaults(person);
            });

            if (options.authorTypes) {
                var sortedAuthors = _.filter(sortedPeople, function(person) {
                    return person.authorType === options.authorTypes.primary;
                });
                var sortedCoAuthors = _.filter(sortedPeople, function(person) {
                    return person.authorType === options.authorTypes.secondary;
                });
                var sortedOthers = _.filter(sortedPeople, function(person) {
                    return (!options.authorTypes || person.authorType === options.authorTypes.none ||
                            (!options.allow.authors && person.isSpeaker));
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
            var $speakerLabel = $('<span>').addClass('i-label small speaker').text($T.gettext("Speaker"));
            var $personRow = $('<div>').addClass('person-row').data('person', person);
            var $personName = $('<div>').addClass('name').text(person.name);
            var $personRoles = $('<span>').addClass('person-roles');
            var $personButtons = $('<span>').addClass('person-buttons');
            var $buttonRemove = $('<a>').addClass('i-link danger icon-close')
                                        .attr('title', $T.gettext("Remove person"));
            var $buttonEdit = $('<a>').addClass('i-link icon-edit')
                                      .attr('title', $T.gettext("Edit information"));
            var $buttonConfig = $('<a>').addClass('i-link icon-settings')
                                        .attr('title', $T.gettext("Configure roles"));

            $personRow.append($personName).append($personRoles).append($personButtons);
            $personButtons.append($buttonRemove).append($buttonEdit);

            if (isSortable) {
                $personRow.prepend('<span class="sort-handle">');
            }

            if (options.allow.submitters) {
                var $submitterLabel = $('<span>').addClass('i-label small submitter')
                                                 .text($T.gettext("Submitter"));
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
            var $buttons = $('<div>');
            var $buttonsSeparator = $('<div>').addClass('titled-rule').text($T.gettext("or"));
            var $submitterLabel = $personRoles.find('.submitter');
            var $speakerLabel = $personRoles.find('.speaker');

            function actionButton(moveText, $targetList, targetData) {
                var $button = $('<div>').addClass('action-row').text(moveText);
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
                    $buttons.append(actionButton($T.gettext("Move to authors"), $authorList, {authorType: 1}));
                }

                if (person.authorType !== options.authorTypes.secondary) {
                    $buttons.append(actionButton($T.gettext("Move to co-authors"), $coauthorList, {authorType: 2}));
                }

                if (options.allow.speakers) {
                    if (person.authorType !== options.authorTypes.none) {
                        $buttons.append(actionButton($T.gettext("Move to others"), $otherList,
                                                     {authorType: 0, isSpeaker: true}));
                        var text = person.isSpeaker ? $T.gettext("Not a speaker anymore")
                                                    : $T.gettext("Make a speaker");

                        $buttons.append($buttonsSeparator);
                        $buttons.append(actionButton(text, null, {isSpeaker: !person.isSpeaker}));

                        $speakerLabel.on('click', function() {
                            $field.principalfield('set', person.id, {isSpeaker: !person.isSpeaker});
                        });
                    } else {
                        $speakerLabel.qtip({
                            content: {
                                text: $T.gettext("People in the 'Others' section <strong>must</strong> be speakers.")
                            },
                            show: {
                                event: 'click',
                                solo: true
                            },
                            hide: {
                                event: 'unfocus click'
                            }
                        });
                    }
                }
            }

            if (options.allow.submitters) {
                var $submitterButton = $('<div>').addClass('action-row');
                $submitterButton.text(person.isSubmitter ? $T.gettext("Revoke submission rights") :
                                                           $T.gettext("Grant submission rights"));
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
                    classes: 'person-link-qbubble'
                },
                content: {
                    text: $buttons
                },
                position: {
                    my: 'left middle',
                    at: 'right middle',
                    adjust: {x: 15}
                },
                events: {
                    show: function() {
                        $element.addClass('active');
                        $element.closest('.person-row').addClass('active');
                    },
                    hide: function() {
                        $element.removeClass('active');
                        $element.closest('.person-row').removeClass('active');
                    }
                }
            });
        }

        $field.principalfield({
            eventId: options.eventId,
            allowExternalUsers: options.allow.externalUsers,
            allowEmptyEmail: options.allow.emptyEmail,
            multiChoice: true,
            overwriteChoice: false,
            render: renderPeople,
            onAdd: function(people) {
                people.forEach(function(person) {
                    if (person.authorType === undefined) {
                        var maxOrder = _.max(people, _.iteratee('displayOrder')).displayOrder || 0;
                        setPersonDefaults(person);
                        person.displayOrder = customOrder ? (maxOrder + 1) : 0;
                    }
                });
            }
        });

        $buttonAddExisting.on('click', function() {
            $field.principalfield('choose');
        });

        $buttonAddNew.on('click', function() {
            $field.principalfield('enter');
        });

        function getSortingMessage()  {
            if (customOrder) {
                return $T.gettext('Custom sorting has been applied. Click to restore alphabetical order.');
            } else {
                return $T.gettext('Alphabetical sorting is ON. Click to turn it off.');
            }
        }

        $buttonAlphaOrder.qtip({content: getSortingMessage});
        $buttonAlphaOrder.on('click', function() {
            var $list = $fieldDisplay.find('.person-list');
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
            var e = $.Event('ajaxForm:validateBeforeSubmit');
            $(this).trigger(e);
            if (e.isDefaultPrevented()) {
                evt.preventDefault();
            }
        });

        $field.closest('form').on('ajaxForm:validateBeforeSubmit', function(evt) {
            var $this = $(this);
            var req = options.require;

            if (req.primaryAuthor || req.secondaryAuthor || req.submitter || req.speaker || !options.allow.speakers) {
                var $formField = $field.closest('.form-field');
                var $formGroup = $field.closest('.form-group');
                var hiddenData = JSON.parse($field.val());
                var hasError = false;

                if (req.speaker && _.indexOf(_.pluck(hiddenData, 'isSpeaker'), true) === -1) {
                    hasError = true;
                    $formField.data('error', $T.gettext('You must add at least one speaker'));
                } else if (req.submitter && _.indexOf(_.pluck(hiddenData, 'isSubmitter'), true) === -1) {
                    hasError = true;
                    $formField.data('error', $T.gettext('You must add at least one submitter'));
                } else if (req.secondaryAuthor && _.indexOf(_.pluck(hiddenData, 'authorType'), 2) === -1) {
                    hasError = true;
                    $formField.data('error', $T.gettext('You must add at least one co-author'));
                } else if (req.primaryAuthor && _.indexOf(_.pluck(hiddenData, 'authorType'), 1) === -1) {
                    hasError = true;
                    $formField.data('error', $T.gettext('You must add at least one author'));
                } else if (!options.allow.speakers && _.indexOf(_.pluck(hiddenData, 'authorType'), 0) !== -1) {
                    hasError = true;
                    $formField.data('error', $T.gettext('You cannot have users in the Other section, please make ' +
                                                        'them authors or co-authors'));
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
    };
})(window);
