/**
 * @author Tom
 */

function readFile(name) {
	var filesystem = new ActiveXObject("Scripting.FileSystemObject");
	var content;
	var f = filesystem.OpenTextFile(name, 1);
	try {
		content = f.ReadAll();
	} finally {
		f.Close();
	}
	return content;
}

function writeFile(name, content) {
	var filesystem = new ActiveXObject("Scripting.FileSystemObject");
	var f = filesystem.CreateTextFile(name, 2);
	try {
		f.Write(content);
	} finally {
		f.Close();
	}
}

var ScriptRoot = "../";

var output = "";

function include(name) {
	output += "\r\n// FILE: " + name + "\r\n";
	output += readFile(name);
}

eval(readFile("Loader.js"));

writeFile("presentation.js", output);
