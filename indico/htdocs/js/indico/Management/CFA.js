
// Class to manage every field limited by words
type("WordsManager", [],
    {

    checkNumWords: function() {
        this.maxWordsCounter.dom.value = this.maxWords - this._numWords(this.element.dom.value);
        this.pm.check();
    },

    _numWords: function(value) {
        return Util.Text.wordsCounter(value);
    },

    _addEvents: function() {
        var self = this;
        this.element.observeEvent('change', function() {self.checkNumWords();});
        this.element.observeEvent('keyup', function() {self.checkNumWords();});
        this.element.observeEvent('blur', function() {self.checkNumWords();});
    },

    checkPM: function() {
        return this.pm.check();
    },


    checkPMEmptyField: function() {
        // Remove the previous pm, check if the field is empty, restore the previous pm
        this.pm.remove(this.element);
        this.pm.add(this.element, null, !this.isMandatory);
        if (this.pm.check()) {
            this.pm.remove(this.element);
            this.initializePM();
            return true;
        } else {
            this.pm.remove(this.element);
            this.initializePM();
            return false;
        }
    },

    initializePM: function() {
        var self = this;
        this.pm.add(this.element, null, !this.isMandatory, function(value) {
            if (self._numWords(value) > self.maxWords) {
                var numExceededWords = self._numWords(value) - self.maxWords;
                if (numExceededWords == 1) {
                    var error = Html.span({}, $T("Maximum number of words has been exceeded in ") + numExceededWords + $T(" word."));
                } else {
                    var error = Html.span({}, $T("Maximum number of words has been exceeded in ") + numExceededWords + $T(" words."));
                }
                return error;
            }
            else {
                self.element.dom.className = '';
                return null;
            }
        });
    }
},

function(element, maxWords, maxWordsCounter, isMandatory) {
    var self = this;
    this.element = element;
    this.maxWords = maxWords;
    this.maxWordsCounter = maxWordsCounter;
    this.isMandatory = isMandatory;
    this.pm = new IndicoUtil.parameterManager();
    this.initializePM();
    this._addEvents();
    this.checkNumWords();
});


//Class to manage every field limited by characters
type("CharsManager", [],
    {

    checkNumChars: function() {
        this.maxCharsCounter.dom.value = this.maxChars - this._numChars(this.element.dom.value);
        this.pm.check();
    },

    _numChars: function(value) {
        return value.length;
    },

    _addEvents: function() {
        var self = this;
        this.element.observeEvent('change', function() {self.checkNumChars();});
        this.element.observeEvent('keyup', function() {self.checkNumChars();});
        this.element.observeEvent('blur', function() {self.checkNumChars();});
    },

    checkPM: function() {
        return this.pm.check();
    },

    checkPMEmptyField: function() {
        // Remove the previous pm, check if the field is empty, restore the previous pm
        this.pm.remove(this.element);
        this.pm.add(this.element, null, !this.isMandatory);
        if (this.pm.check()) {
            this.pm.remove(this.element);
            this.initializePM();
            return true;
        } else {
            this.pm.remove(this.element);
            this.initializePM();
            return false;
        }
    },

    initializePM: function() {
        var self = this;
        this.pm.add(this.element, null, !this.isMandatory, function(value) {
            if (self._numChars(value) > self.maxChars) {
                var numExceededChars = self._numChars(value) - self.maxChars;
                if (numExceededChars == 1) {
                    var error = Html.span({}, $T("Maximum number of characters has been exceeded in ") + numExceededChars + $T(" character."));
                } else {
                    var error = Html.span({}, $T("Maximum number of characters has been exceeded in ") + numExceededChars + $T(" characters."));
                }
                return error;
            } else {
                self.element.dom.className = '';
                return null;
            }
        });
        return false;
    }
},

function(element, maxChars, maxCharsCounter, isMandatory) {
    this.element = element;
    this.maxChars = maxChars;
    this.maxCharsCounter = maxCharsCounter;
    this.isMandatory = isMandatory;
    this.pm = new IndicoUtil.parameterManager();
    this.initializePM();
    this._addEvents();
    this.checkNumChars();
});
