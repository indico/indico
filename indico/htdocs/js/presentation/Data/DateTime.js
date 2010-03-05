/**
 * DateTime
 * @author Tom
 */

// acceptable formats:
//  'h', 'hh', 'hmm', 'hhmm',
//  'h+', 'hh+', 'h+m', 'h+mm', 'hh+m', 'hh+mm'
// returns [h, m]

/**
 * Parses time from the text.
 * @param {String} text
 * @return {Array}
 */
function parseTime(text) {
        text = trim(text);
        if (text == "") {
                return null;
        }
        var hour = 0;
        var min = 0;
        if (/^\d{1,4}$/.test(text)) {
        // 'h', 'hh', 'hmm', 'hhmm'
                switch (text.length) {
                        case 1:
                                hour = parseInt(text, 10);
                                break;
                        case 2:
                                hour = parseInt(text.substr(0, 2), 10);
                                break;
                        case 3:
                                hour = parseInt(text.substr(0, 1), 10);
                                min = parseInt(text.substr(1, 2), 10);
                                break;
                        case 4:
                                hour = parseInt(text.substr(0, 2), 10);
                                min = parseInt(text.substr(2, 2), 10);
                                break;
                }
        } else {
                var match = /^(\d{1,2})[\W]+(\d{1,2})?$/.exec(text);
                if (!match) {
                        return null;
                }
                // 'h+', 'hh+', 'h+M', 'h+mm', 'hh+M', 'hh+mm'
                hour = parseInt(match[1], 10);
                var minText = any(match[2], "");
                if (minText != "") {
                        min = parseInt(minText, 10);
                }
        }
        return [hour, min];
}

// hh:mm
/**
 * Formats time.
 * @param {Date} time
 * @return {String}
 */
function formatTime(time) {
        return time.getHours().toString() + ":"
                + time.getMinutes().toPaddedString(2);
}

// tuple is [hour, min, sec, msec]
/**
 * Sets the time from the tuple.
 * @param {Date} time
 * @param {Array} tuple
 */
function setTime(time, tuple) {
        time.setHours(
                any(tuple[0], 0),
                any(tuple[1], 0),
                any(tuple[2], 0),
                any(tuple[3], 0)
        );
}

// returns [hour, min, sec, msec]
/**
 * Returns a tuple from the time.
 * @param {Date} time
 * @return {Array}
 */
function getTime(time) {
        return [
                time.getHours(),
                time.getMinutes(),
                time.getSeconds(),
                time.getMilliseconds()
        ];
}

// acceptable formats:
//  'd', 'dm', 'ddm', 'ddmm',
//      'ddmmy', 'ddmmYY', 'ddmmyyy', 'ddmmyyyy',
//      'd+', d+m', 'd+m+', 'd+m+YY', 'd+m+y'
//  YY - current century
// returns [d, m, y]

/**
 * Parses date from the text.
 * @param {String} text
 * @return {Array}
 */
function parseDate(text) {
        text = trim(text);
        if (text == "") {
                return null;
        }
        var day = null;
        var month = null;
        var year = null;
        if (/^\d{1,8}$/.test(text)) {
                // 'd', 'dm', 'ddm', 'ddmm', 'ddmmY', 'ddmmYY', 'ddmmyyy', 'ddmmyyyy'
                switch (text.length) {
                        case 1:
                                day = parseInt(text.substr(0, 1), 10);
                                break;
                        case 2:
                                day = parseInt(text.substr(0, 1), 10);
                                month = parseInt(text.substr(1, 1), 10);
                                break;
                        case 3:
                                day = parseInt(text.substr(0, 2), 10);
                                month = parseInt(text.substr(2, 1), 10);
                                break;
                        case 4:
                                day = parseInt(text.substr(0, 2), 10);
                                month = parseInt(text.substr(2, 2), 10);
                                break;
                        case 5:
                                day = parseInt(text.substr(0, 2), 10);
                                month = parseInt(text.substr(2, 2), 10);
                                year = [parseInt(text.substr(4, 1), 10)];
                                break;
                        case 6:
                                day = parseInt(text.substr(0, 2), 10);
                                month = parseInt(text.substr(2, 2), 10);
                                year = [parseInt(text.substr(4, 2), 10)];
                                break;
                        case 7:
                                day = parseInt(text.substr(0, 2), 10);
                                month = parseInt(text.substr(2, 2), 10);
                                year = parseInt(text.substr(4, 3), 10);
                                break;
                        case 8:
                                day = parseInt(text.substr(0, 2), 10);
                                month = parseInt(text.substr(2, 2), 10);
                                year = parseInt(text.substr(4, 4), 10);
                                break;
                }
        } else {
                var match = /^(\d{1,2})[\W]+((\d{1,2})([\W]+(\d{1,4})?)?)?$/.exec(text);
                if (!match) {
                        return null;
                }
                // 'd+', d+m', 'd+m+', 'd+m+YY', 'd+m+y'
                day = parseInt(match[1], 10);
                var monthText = any(match[3], "");
                if (monthText != "") {
                        month = parseInt(monthText, 10);
                }
                var yearText = any(match[5], "");
                if (exists(yearText)) {
                        year = parseInt(yearText, 10);
                        if (yearText.length < 3) {
                                year = [year];
                        }
                }
        }
        return [day, month, year];
}

// d.m.yyyy
/**
 * Formats date.
 * @param {Date} date
 * @return {String}
 */
function formatDate(date) {
        return date.getDate().toString() + "."
                + (date.getMonth() + 1).toString() + "."
                + date.getFullYear().toPaddedString(3);
}

// tuple is [day, month, year]
/**
 * Sets the date from the tuple.
 * @param {Date} date
 * @param {Array} tuple
 */
function setDate(date, tuple) {
        var day = tuple[0];
        var month = tuple[1];
        var year = tuple[2];
        if (exists(year)) {
                if (isArray(year)) {
                        year = Math.floor(date.getFullYear() / 100) * 100       + year[0]
                }
                date.setFullYear(year);
        }
        if (exists(month)) {
                date.setMonth(month - 1);
        }
        if (exists(day)) {
                date.setDate(day);
        }

}

// returns [day, month, year]
/**
 * Returns a tuple from the date.
 * @param {Date} date
 * @retrun {Array}
 */
function getDate(date) {
        return [
                date.getDate(),
                date.getMonth() + 1,
                date.getFullYear()
        ];
}

function __test__parseTime() {
        var results = [];
        iterate([
    ["1", 1, 0],
    ["12", 12, 0],
    ["27", 27, 0],
    ["123", 1, 23],
    ["023", 0, 23],
    ["1234", 12, 34],
    ["0034", 0, 34],
    ["1:", 1, 0],
    ["12:", 12, 0],
    ["3:4", 3, 4],
    ["12:3", 12, 3],
    ["02:3", 2, 3],
    ["12:34", 12, 34],
    ["00:34", 0, 34]
        ], function(item) {
                var result = parseTime(item[0]);
                if (result == null) {
                        if (item[1] != null) {
                                results.push(format("{0}> {1}:{2} != null", [item[0], item[1], item[2]]));
                        }
                } else {
                        if (result[0] != item[1] || result[1] != item[2]) {
                                results.push(format("{0}> {1}:{2} != {3}:{4}", [item[0], item[1], item[2], result[0], result[1]]));
                        }
                }
        });
        return results;
}

function __test__parseDate() {
        var results = [];
        iterate([
                ["2", 2, null, null],
                ["23", 2, 3, null],
                ["231", 23, 1, null],
                ["2310", 23, 10, null],
                ["23104", 23, 10, [4]],
                ["231045", 23, 10, [45]],
                ["2310456", 23, 10, 456],
                ["23104567", 23, 10, 4567],
                ["23107", 23, 10, [7]],
                ["231007", 23, 10, [7]],
                ["2310007", 23, 10, 7],
                ["23100007", 23, 10, 7],
                ["30.", 30, null, null],
                ["2.10", 2, 10, null],
                ["23.1", 23, 1, null],
                ["23.10", 23, 10, null],
                ["30.12.", 30, 12, null],
                ["2.10.4", 2, 10, [4]],
                ["23.1.4", 23, 1, [4]],
                ["2.10.45", 2, 10, [45]],
                ["23.1.45", 23, 1, [45]],
                ["23.10.45", 23, 10, [45]],
                ["2.10.4567", 2, 10, 4567],
                ["23.1.4567", 23, 1, 4567],
                ["23.10.4567", 23, 10, 4567]
        ], function(item) {
                var result = parseDate(item[0]);
                if (result == null) {
                        if (item[1] != null) {
                                results.push(format("{0}> {1}.{2}.{3} != null", [item[0], item[1], item[2], item[3]]));
                        }
                } else {
                        if (result[0] != item[1] || result[1] != item[2] || (result[2] != item[3]
                                        && (result[2] != null && item[3] != null && result[2][0] != item[3][0]))) {
                                results.push(format("{0}> {1}.{2}.{3} != {4}.{5}.{6}", [item[0], item[1], item[2], item[3], result[0], result[1], result[2]]));
                        }
                }
        });
        return results;
}
