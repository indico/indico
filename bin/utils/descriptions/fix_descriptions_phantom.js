var system = require('system');
var webpage = require('webpage');
var fs = require('fs');

var page = webpage.create();
page.onConsoleMessage = function(message) {
    system.stderr.writeLine(message);
};
page.onCallback = function(cmd, arg) {
    if (cmd == 'sql') {
        console.log(arg);
    } else if (cmd == 'exit') {
        phantom.exit();
    }
};

content = fs.read('/dev/stdin');
if (content == '') {
    phantom.exit();
}
page.content = content;
