// Extended Tooltip Javascript
// copyright 9th August 2002, 3rd July 2005
// by Stephen Chapman, Felgall Pty Ltd

// permission is granted to use this javascript provided that the below code is not altered
var DH = 0;
var an = 0;
var al = 0;
var ai = 0;
if (document.getElementById) 
{
    ai = 1; 
    DH = 1;
}
else 
{
    if (document.all) 
    {
        al = 1; DH = 1;
    } 
    else 
    { 
        browserVersion = parseInt(navigator.appVersion); 
        if ((navigator.appName.indexOf('Netscape') != -1) && (browserVersion == 4)) 
        {
            an = 1; DH = 1;
        }
    }
} 

function fd(oi, wS) 
{
    if (ai) 
        return wS ? document.getElementById(oi).style:document.getElementById(oi); 
    if (al) 
        return wS ? document.all[oi].style: document.all[oi]; 
    if (an) 
        return document.layers[oi];
}

function pw() 
{
    return window.innerWidth != null? window.innerWidth: document.body.clientWidth != null? document.body.clientWidth:null;
}

function mouseX(evt) 
{
    if (evt.pageX) 
        return evt.pageX; 
    else 
        if (evt.clientX)
            return evt.clientX + (document.documentElement.scrollLeft ?  document.documentElement.scrollLeft : document.body.scrollLeft); 
        else return null;
}

function mouseY(evt) 
{
    if (evt.pageY) 
        return evt.pageY; 
    else  // IE
        if (evt.clientY)
            return evt.clientY + (document.documentElement.scrollTop ? document.documentElement.scrollTop : document.body.scrollTop); 
        else return null;
}
function popUp(evt,oi) 
{
    if (DH) 
    {
        var wp = pw(); 
        ds = fd(oi,1); 
        dm = fd(oi,0); 
        st = ds.visibility; 
        if (dm.offsetWidth) 
            ew = dm.offsetWidth; 
        else 
            if (dm.clip.width) 
                ew = dm.clip.width; 
        if (st == "visible" || st == "show") 
        {
            ds.visibility = "hidden"; 
        } 
        else 
        {
            tv = mouseY(evt) + 20; 
            lv = mouseX(evt) - (ew/4); 
            if (lv < 2) 
                lv = 2; 
            else 
                if (lv + ew > wp) 
                    lv -= ew/2; 
            if (!an) 
            {
                lv += 'px';
                tv += 'px';
            }
            ds.left = lv; 
            ds.top = tv; 
            ds.visibility = "visible";
        }
    }
}
