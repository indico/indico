/**
 * Text
 * @author Tom
 */

/**
 * Loads dictionary for given language
 * @param {String} language
 */
function loadDictionary(language) {
        include(languageDictionaryPath + language + ".js");
}

var defaultLanguage = "en_US";
var languageDictionaryPath = isDefined("TextRoot") ? TextRoot : "texts";
var json_locale_data = {};

var currentLanguage = null;

/**
 * Returns text from template for given key and params
 * @param {String} key
 * @param {String} ... params
 * @return {String} text
 */
function $T(key){
    if (json_locale_data[key]) {
        return json_locale_data[key][1];
    } else {
        return key;
    }
}


String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
        return typeof args[number] != 'undefined' ? args[number] : '{' + number + '}';
    });
};
