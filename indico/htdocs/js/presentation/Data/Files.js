/**
 * @author Tom
 */

// Currently only IE
var File = {};

File.getSystem = function() {
	return obtain(File, "FileSystemObject", function() {
		return new ActiveXObject("Scripting.FileSystemObject");
	});
};

File.read = function(name) {
	var f = File.getSystem().OpenTextFile(name, 1);
	var content;
	try {
		content = f.ReadAll();
	} finally {
		f.Close();
	}
	return content;
};

File.write = function(name, content) {
	var f = File.getSystem().OpenTextFile(name, 2, true);
	try {
		f.Write(content);
	} finally {
		f.Close();
	}
};

File.append = function(name, content) {
	var f = File.getSystem().OpenTextFile(name, 8, true);
	try {
		f.Write(content);
	} finally {
		f.Close();
	}
};

File.exists = function(name) {
	return File.getSystem().FileExists(name);
};