/* This file is part of Indico.
 * Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

/**
 * Builds a widget with page numbers, to put at the bottom of paginated results.
 * @param {Integer or String with an Integer} nPages : The total number of pages through which we want to browse.
 * @param {Integer or String with an Integer}selectedPage : The currently selected page.
 * @param {Integer or String with an Integer}around : Number of pages that we want to whow to each side of the selected page. Note: if the selected page is 1,
 *               it will have around * 2 pages on its right.
 * @param {function} handler : a function that will be called everytime the user clicks on a page number. The function will be passed
 *                             the clicked number.
 * 
 * The resulting object has the following methods:
 * -draw() : returns the HTML that renders the widget.
 * -setNumberOfPages(Integer or String with an Integer): to change the number of pages of an existing widget.
 * -selectPage(Integer or String with an Integer): to change the currently selected page. This will call refresh()
 * -refresh(): redraws the widget in-place.
 * -getNumberOfPages(): gets the current number of pages.
 * -getSelectedPage(): gets the currently selected page.
 */
type("PageFooter", [], 
    {
        getNumberOfPages: function() {
            return this.nPages;
        },
    
        setNumberOfPages: function(nPages) {
            nPages = parseInt(nPages);
            this.nPages = nPages;
            this.selectedPage = 1;
        },
        
        getSelectedPage: function() {
            return this.selectedPage;
        },
        
        selectPage: function(page) {
            page = parseInt(page);
            this.selectedPage = page;
            this.refresh()
        },
        
        refresh: function() {
            var self = this;

            var pages = makePageList(this.nPages, this.selectedPage, this.around);
            
            if (this.nPages > 1) {
                if (this.hidden) {
                    IndicoUI.Effect.appear(this.content);
                    this.hidden = false;
                }
                this.content.clear();
                
                each(pages, function(i){
                	var page = Html.a(i == self.selectedPage ? 'pageSelected' : 'pageUnselected', i);
                	page.observeClick(function(){
                		self.handler(i);
                	});
                    self.content.append(Html.li('pageNumber' + (i == self.nPages ? ' lastPageNumber' : ''), page))
                });
            } else {
                this.hidden = true;
                IndicoUI.Effect.disappear(this.content);
            }
        },
    
        draw: function() {
            this.content = Html.ul('pageNumberList');
            this.refresh();
            return this.content;
        }
    },
    function(nPages, initialPage, around, handler) {
        this.nPages = parseInt(nPages);
        if (!this.nPages) {this.nPages = 1}
        this.selectedPage = parseInt(initialPage);
        if (!this.selectedPage) {this.selectedPage = 1}
        this.around = around;
        if (!this.around) {this.around = 4}
        
        this.handler = handler;
        
        this.hidden = false;        
    }
);
