/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

/**
 * Returns a list of page numbers
 * @param nPages The total number of pages through which we want to browse.
 * @param selectedPage The currently selected page.
 * @param around Number of pages that we want to whow to each side of the selected page. Note: if the selected page is 1,
 *               it will have around * 2 pages on its right.
 * @return A list with the page numbers that should appear on the page number widget.
 */
var makePageList = function(nPages, selectedPage, around) {
    var result = [];

    result.push(selectedPage);

    var min = selectedPage;
    var max = selectedPage;

    // create the near pages
    var remaining = around * 2;
    var i = 1;

    while (remaining > 0 && (min > 1 || max < nPages)) {
        if (selectedPage - i > 0) {
        	min = selectedPage - i;
            result.push(min);
            remaining--;
        }
        if (selectedPage + i <= nPages) {
        	max = selectedPage + i;
            result.push(max);
            remaining--;
        }
        i++;
    }

    // create the far pages
    var roundTo10 = function(n) {
        var remainder = n % 10;
        return (n - remainder);
    };

    min = roundTo10(min - 1);
    max = roundTo10(max + 10);

    var firstInserted = false;
    var lastInserted = false;

    for (i = 0; i < around/2; i++) {
    	if (min > 0) {
    		result.push(min)
    	}
    	if (max <= nPages) {
    		result.push(max)
    	}
    	min -= 10;
    	max += 10;
    }

    result.sort(numberSorter);

    if (result[result.length - 1] != nPages) {
    	result.push(nPages)
    }
    if (result[0] != 1) {
    	result.push(1);
    	result.sort(numberSorter);
    }

    return result;
};
