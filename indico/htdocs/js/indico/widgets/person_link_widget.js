/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

(function(global) {
    'use strict';

    global.setupPersonLinkWidget = function setupPersonLinkWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            eventId: null,
            authorTypes: null,
            showEmptyCoauthors: true,
            allow: {
                authors: false,
                submitters: false,
                emptyEmail: false,
                externalUsers: true
            },
            defaults: {
                authorType: 0,
                isSpeaker: false,
                isSubmitter: false
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

        function renderPeople(people) {
            $authorList.html('');
            $coauthorList.html('');
            $otherList.html('');
            _.each(people, renderPerson);
            $noAuthorPlaceholder.toggle($authorList.is(':empty'));
            if (!options.showEmptyCoauthors) {
                $coauthorListTitle.toggle($coauthorList.is(':not(:empty)'));
            } else {
                $noCoauthorPlaceholder.toggle($coauthorList.is(':empty'));
            }
            $otherListTitle.toggle($otherList.is(':not(:empty)'));
            $noOtherPlaceholder.toggle($otherList.is(':empty'));
        }

        function renderPerson(person) {
            var $personRow = $('<div>').addClass('person-row');
            var $personName = $('<div>').addClass('name').text(person.name);
            var $personRoles = $('<span>').addClass('person-roles');
            var $personButtons = $('<span>').addClass('person-buttons');
            var $buttonRemove = $('<a>').addClass('i-button-icon danger icon-close').attr('title', $T.gettext("Remove person"));
            var $buttonEdit = $('<a>').addClass('i-button-icon icon-edit').attr('title', $T.gettext("Edit information"));
            var $buttonConfig = $('<a>').addClass('i-button-icon icon-settings').attr('title', $T.gettext("Configure roles"));

            setPersonDefaults(person);
            $personRow.append($personName).append($personRoles).append($personButtons);
            $personButtons.append($buttonRemove).append($buttonEdit);

            if (options.allow.submitters) {
                var $submitterLabel = $('<span>').addClass('i-label small submitter').text($T.gettext("Submitter"));
                $personRoles.append($submitterLabel.toggleClass('selected', person.isSubmitter));
            }

            if (options.allow.authors) {
                var $speakerLabel = $('<span>').addClass('i-label small speaker').text($T.gettext("Speaker"));
                $personRoles.prepend($speakerLabel.toggleClass('selected', person.isSpeaker));
            }

            if (!options.authorTypes || person.authorType == options.authorTypes.none || (!options.allow.authors && person.isSpeaker)) {
                $otherList.append($personRow);
                if (options.allow.authors) {
                    $speakerLabel.addClass('other');
                }
            } else if (person.authorType == options.authorTypes.primary) {
                $authorList.append($personRow);
            } else if (person.authorType == options.authorTypes.secondary) {
                $coauthorList.append($personRow);
            }

            if (options.allow.submitters || options.allow.authors) {
                $personButtons.append($buttonConfig);
                setupPersonConfig(person, $buttonConfig, $personRoles);
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
        }

        function setupPersonConfig(person, $element, $personRoles) {
            var $buttons = $('<div>');
            var $buttonsSeparator = $('<div>').addClass('titled-rule').text($T.gettext("or"));
            var $submitterLabel = $personRoles.find('.submitter');
            var $speakerLabel = $personRoles.find('.speaker');

            if (options.allow.authors) {
                if (person.authorType != options.authorTypes.primary) {
                    var $authorButton = $('<div>').addClass('action-row').text($T.gettext("Move to authors"));
                    $authorButton.on('click', function() {
                        $element.qbubble('hide');
                        $field.principalfield('set', person.id, {authorType: 1});
                    });
                    $buttons.append($authorButton);
                }

                if (person.authorType != options.authorTypes.secondary) {
                    var $coAuthorButton = $('<div>').addClass('action-row').text($T.gettext("Move to co-authors"));
                    $coAuthorButton.on('click', function() {
                        $element.qbubble('hide');
                        $field.principalfield('set', person.id, {authorType: 2});
                    });
                    $buttons.append($coAuthorButton);
                }

                if (person.authorType != options.authorTypes.none) {
                    var $nonAuthorButton = $('<div>').addClass('action-row').text($T.gettext("Move to others"));
                    $nonAuthorButton.on('click', function() {
                        $element.qbubble('hide');
                        $field.principalfield('set', person.id, {authorType: 0, isSpeaker: true});
                    });
                    var $speakerButton = $('<div>').addClass('action-row');
                    $speakerButton.text(person.isSpeaker ? $T.gettext("Not a speaker anymore") : $T.gettext("Make a speaker"));
                    $speakerButton.on('click', function() {
                        $element.qbubble('hide');
                        $field.principalfield('set', person.id, {isSpeaker: !person.isSpeaker});
                    });
                    $buttons.append($nonAuthorButton).append($buttonsSeparator).append($speakerButton);
                    $speakerLabel.on('click', function() {
                        $field.principalfield('set', person.id, {isSpeaker: !person.isSpeaker});
                    });
                } else {
                    $buttons.append($buttonsSeparator);
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

            if (options.allow.submitters) {
                var $submitterButton = $('<div>').addClass('action-row');
                $submitterButton.text(person.isSubmitter ? $T.gettext("Revoke submission rights") : $T.gettext("Grant submission rights"));
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
            render: function(people) {
                renderPeople(people);
            }
        });

        $buttonAddExisting.on('click', function() {
            $field.principalfield('choose');
        });

        $buttonAddNew.on('click', function() {
            $field.principalfield('enter');
        });
    };
})(window);
