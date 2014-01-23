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

type('IntelligentSearchBox', ['RealtimeTextBox'],
     {
         _highlight: function(elem, token) {
             // Code for highlighting the matched part of the string
             var idx = elem.toLowerCase().indexOf(token.toLowerCase());
             if (idx >= 0) {
                 var before = elem.slice(0, idx);
                 var after = elem.slice(idx+token.length, elem.length);
                 return [before, Html.span("searchSuggestionHighlight", elem.slice(idx,idx+token.length)), after];

             }
         },

         _truncateTitle: function(title) {
             var max = 27;
             if (title.length > max) {

                 return title.slice(0,max/2) + ' ... ' +
                     title.slice(-max/2);

             } else {
                 return title;
             }
         },

         _showSuggestions: function(text, suggList, totalNumber) {

             var self= this;

             if (!this.suggestionBox) {
                 // Create the suggestion box only once

                 // totalNumber will change during time
                 this.totalNumber = new WatchValue(totalNumber);
                 this.suggestionList = Html.ul('suggestionBoxList');

                 var infoBox = Html.div('searchSuggestionHelpBox',
                     $T("Some category suggestions..."));

                 // Create the suggestion box
                 this.suggestionBox = Html.div({ style: {position: 'absolute',
                                                         top: pixels(23),
                                                         left: 0
                                                        },
                                                 className: 'suggestionBox'},
                                               infoBox,
                                               this.suggestionList,
                                               $B(Html.div("searchSuggestionOtherResults"), this.totalNumber, function(number) {return number===0?'':number + ' ' + $T('other results - please write more...'); })
                                              );

                 this.container.append(this.suggestionBox);
             }

             // Prepare regular expression for highlighting
             var tokens = filter(escapeHTML(text).split(' '), function(t) { return t !== '';});
             var tokenRE = new RegExp("("+tokens.join('|')+")", 'gi');


             // Bind the list to the DOM element

             var counter = 0;

             $B(this.suggestionList, suggList,
                function(elem) {
                    var titleHtml = escapeHTML(self._truncateTitle(elem.title)).replace(tokenRE, '<span class="searchSuggestionHighlight">$1</span>');

                    var index = counter;

                    var title = Html.span('searchSuggestionTitle');
                    title.dom.innerHTML = titleHtml;
                    var pathText = Util.truncateCategPath(elem.path).join(' >> ');
                    var path = Html.div('searchSuggestionPath', pathText);
                    var liItem = Html.li({}, title, path);

                    // Use mouse to control selector as well

                    liItem.observeEvent('mouseover', function() {
                        if (self.selectorPos != index) {
                            self._clearSelector();
                            self.selectorPos = index;
                            self._setSelector();
                        }
                    });

                    liItem.observeClick(function() {
                        window.location = elem.url;
                    });


                    counter++;

                    return liItem;
                });

             this.suggestionList.observeEvent('mouseout', function() {
                 self._clearSelector();
                 self.selectorPos = -1;
             });


             // Update
             this.totalNumber.set(totalNumber);
         },

         _hideSuggestions: function() {
             this.container.remove(this.suggestionBox);
             this.suggestionBox = null;
             this.selectorPos = -1;
             this.suggestions = null;
         },

         _retrieveOptions: function(expression) {
             this.querying = true;
             var self = this;

             indicoRequest('search.categoryName',
                           {value: expression},
                           function(result, error) {

                               self.querying = false;
                               self.timeOfLastQuery = (new Date()).getTime();

                               if (!error) {
                                   if (result.list.length > 0) {
                                       self.suggestions = result.list;
                                       self._showSuggestions(expression, result.list, result.number - result.list.length);
                                   } else {
                                       self._hideSuggestions();
                                   }

                                   currentText = trim(self.get());

                                   // if the text changed meanwhile and it
                                   // is still long enough
                                   if (currentText != expression &&
                                       currentText.length > 1) {
                                       // request
                                       self._textTyped()
                                   } else if (currentText.length <= 1){
                                       // if it is not long enough
                                       self._hideSuggestions();
                                   }
                               } else {
                                   IndicoUtil.errorReport(error);
                               }
                           });
         },

         _getTimeSinceLastQuery: function() {
             var now = new Date();
             return now.getTime() - this.timeOfLastQuery;
         },

         _waitForRequestTime: function() {
             var self = this;
             if (!this.queuedRequest) {
                 // This should never happen...
                 return;
             }

             if (this._getTimeSinceLastQuery() > 1000) {
                 this._textTyped();
                 this.queuedRequest = false;
             } else {
                 setTimeout(function() {
                         self._waitForRequestTime();
                     }, 300);
             }
         },

         /*
          * Called each time a new character is typed
          * strips white spaces, and calls for a request if needed
          */
         _textTyped: function(key) {

             var self = this;
             var text = trim(this.get());

             if(text.length > 1) {

                 // if we're not already querying and enough time has passed
                 // since the last request
                 if(!this.querying && this._getTimeSinceLastQuery() > 1000) {
                     this._retrieveOptions(text);
                 } else if (!this.queuedRequest) {
                     // otherwise, if we can't do a request right now
                     // and no other request is queued
                     this.queuedRequest = true;

                     setTimeout(function() {
                             self._waitForRequestTime();
                         }, 300);
                 }
             } else if (this.suggestionBox) {
                 this._hideSuggestions();
             }
         },

         _openSelection: function(event) {
             if (this.selectorPos >= 0) {
                 window.location = this.suggestions[this.selectorPos].url;
                 return false;
             }
             return true;
         },

         /*
          * Move the selector (gray area) up or down
          */
         _moveSelector: function(direction) {

             if (this.suggestionBox) {
                 var suggNum = this.suggestionList.length.get();

                 if(this.selectorPos < 0) {
                     this.selectorPos = direction=='down'?0:suggNum-1;
                 } else {
                     this._clearSelector();
                     this.selectorPos += direction=='up'?-1:1;

                     if (this.selectorPos >= suggNum) {
                         this.selectorPos = -1;
                     } else if (this.selectorPos < 0) {
                         this.selectorPos = -1;
                     }
                 }
             }

             this._setSelector();
         },

         _setSelector: function() {
             if (this.selectorPos >= 0) {
                 this.suggestionList.item(this.selectorPos).dom.className = 'searchSuggestionSelected';
             }
         },

         _clearSelector: function() {
             if (this.selectorPos >= 0) {
                 this.suggestionList.item(this.selectorPos).dom.className = '';
             }
         },

         isAnyItemSelected: function(){
             return this.selectorPos > 0;
         }

     },
     function(args, container, submitBtn){
         args.autocomplete = 'off';
         this.RealtimeTextBox(args);
         this.selectorPos = -1;
         this.querying = false;
         this.container = container;
         this.timeOfLastQuery = 0;

         var self = this;

         this.observe(function(key, event) {
             self._textTyped(key);
             return true;
         });

         this.observeOtherKeys(function(text, key, event) {
             if (key == 38 || key == 40) {
                 self._moveSelector(key==38?'up':'down');
                 return false;
             } else if (key == 27) {
                 self._hideSuggestions();
                 return false;
             } else if (key == 13) {
                 return self._openSelection(event);
             } else {
                 return true;
             }
         });

         $E(document.body).observeClick(function(event) {
             // Close box if a click is done outside of it

             /* for some unknown reason, onclick is called on the submit button,
              * as soon as the return key is pressed in any of the textfields.
              * To make it even better, onclick is called before onkeyup,
              * which forces us to do the last two checks.
y              */

             if (self.suggestionBox &&
                 !self.suggestionList.ancestorOf($E(eventTarget(event))) &&
                 $E(eventTarget(event)) != self.input &&
                 $E(eventTarget(event)) != submitBtn)
             {
                 self._hideSuggestions();
             }
         });

     }
    );


$.widget('ui.search_tag', {
    options: {
        categ_title: 'Home',
        everywhere: true,
        categ_id: 0
    },

    _transition: function(title, no_check) {
        var $tag = this.$tag;
        var old_width = $tag.width()

        $tag.fadeTo('fast', 0.3).width('').find('.where').html(title);
        var new_width = $tag.width();

        // store target width
        $tag.fadeTo('fast', 0.5).width(old_width).data('target-width', new_width);

        $tag.animate({
            width: ((new_width < old_width) && !no_check) ? old_width : new_width
        }, 200, 'linear');

    },

    _create: function() {
        var self = this;

        var tag_template = _.template('<div class="searchTag">' +
                                      '<div class="cross">x</div>' +
                                      '<div class="where"><%= categ_title %></div>' +
                                      '</div>');

        var $tag = this.$tag = $(tag_template({
            categ_title: this.options.everywhere ? $T('Everywhere') : this.options.categ_title
        }));

        $(this.element).replaceWith($tag);
        var $where = $('.where', $tag);

        this.initial_width = this.$tag.width();

        if (this.options.everywhere) {
            $tag.addClass('everywhere');
            $('.cross', this.$tag).hide();
        } else {
            $tag.addClass('inCategory');
            $('.cross', this.$tag).show();
        }

        $('.cross', $tag).on('click', function() {
            self.search_everywhere();
        });

        var $parent = $tag.parent();

        $parent.on('mouseenter', '.searchTag.everywhere', function() {
            self.show_categ();
        });
        $parent.on('mouseover', '.searchTag.everywhere', function(event) {
            self.show_tip(event);
        });
        $parent.on('mouseleave', '.searchTag.everywhere', function() {
            $where.removeClass('hasFocus');
        });
        $parent.on('click', '.searchTag.inCategoryOver', function() {
            self.confirm_tip();
        });
        $parent.on('mouseleave', '.searchTag.inCategoryOver', function() {
            self.back_to_everywhere();
        });
    },

    confirm_tip: function() {
        var $where = $('.where', this.$tag)
        var $tag = this.$tag;

        $tag.qtip('destroy');
        $where.fadeOut('fast', function() {
            $(this).fadeIn('fast');
        });

        this.$tag.addClass('inCategory').removeClass('everywhere').removeClass('inCategoryOver');
        this.options.input.attr('value', this.options.categ_id);

        // use target-width as searchTag may still be growing
        $tag.animate({
            width: $tag.data('target-width') + $('.cross', $tag).width() + 10
        }, 200, 'swing', function(){
            $('.cross', $tag).fadeIn('fast');
        });
    },

    search_everywhere: function() {
        $('.cross', this.$tag).hide();
        this.$tag.addClass('everywhere').removeClass('inCategory');
        this._transition($T('Everywhere'), true);
        this.options.input.attr('value', 0);
    },

    show_categ: function() {
        var $tag = this.$tag;
        var $where = $('.where', $tag)
        var self = this;
        $where.addClass('hasFocus');
        setTimeout(function(){
            if ($where.hasClass('hasFocus')) {
                self._transition(self.options.categ_title);
                $tag.addClass('inCategoryOver');
            }
        }, 200);
    },

    show_tip: function(event) {
        this.$tag.qtip({
            content: format($T('Click to search inside <span class="label">{title}</span>'),
                              {title: this.options.categ_title}),
            position:{
                at: 'bottom center',
                my: 'top center'
            },
            style: {
                classes: 'qtip-shadow'
            },
            show: {
                event: event.type,
                ready: true
            }
        }, event);
    },

    back_to_everywhere: function() {
        var $where = $('.where', this.$tag);
        var self = this;

        this.$tag.removeClass('inCategoryOver');
        $where.removeClass('hasFocus');
        setTimeout(function(){
            if (!$where.hasClass('hasFocus')) {
                self._transition($T('Everywhere'), true);
                self.$tag.addClass('everywhere');
            }
        }, 200);
    }
});
