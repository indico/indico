/**
 * @author Tom
 */

function MimeType(name, classid, codebase, url) {
	this.name = name;
	this.classid = classid;
	this.codebase = codebase;
	this.url = url;
}

MimeType.QuickTime = new MimeType("image/x-quicktime", "clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B", "http://www.apple.com/qtactivex/qtplugin.cab", "http://www.apple.com/quicktime/download/");
MimeType.RealPlayer = new MimeType("audio/x-pn-realaudio-plugin", "clsid:CFCDAA03-8BE4-11cf-B84B-0020AFBBCCFA", null, null);
MimeType.Flash = new MimeType("application/x-shockwave-flash", "clsid:D27CDB6E-AE6D-11cf-96B8-444553540000", "http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab", "http://www.macromedia.com/go/getflashplayer");
