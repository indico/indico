/* This file is part of Indico.
 * Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
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

var baseDirs = {
    imageRegForm           : ScriptRoot + "/indico/RegistrationForm/images/"
};

var regForm = {
        icons : {
            checkbox        : baseDirs.imageRegForm + "checkbox.png",
            country         : baseDirs.imageRegForm + "country.png",
            date            : baseDirs.imageRegForm + "date.png",
            dropdown_menu   : baseDirs.imageRegForm + "dropdown_menu.png",
            file            : baseDirs.imageRegForm + "file.png",
            label           : baseDirs.imageRegForm + "label.png",
            phone           : baseDirs.imageRegForm + "phone.png",
            radio_list      : baseDirs.imageRegForm + "radio_list.png",
            text            : baseDirs.imageRegForm + "text.png",
            textarea        : baseDirs.imageRegForm + "textarea.png",
            yesno           : baseDirs.imageRegForm + "yesno.png",
            number          : baseDirs.imageRegForm + "number.png"
        },
        classes : {
            section                 : "regFormSection",
            header                  : "regFormHeader",
            title                   : "regFormSectionTitle",
            description             : "regFormSectionDescription",
            content                 : "regFormSectionContent",
            field                   : "regFormField",
            fieldDisabled           : "regFormFieldDisabled",
            text                    : "regFormText",
            currency                : "regFormCurrency",
            price                   : "regFormPrice",
            billable                : "regFormIsBillable",
            contentIsDragAndDrop    : "regFormIsDragAndDrop"
        }
};