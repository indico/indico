/** $Id: alphaAPI.js 1940 2005-07-16 23:23:54Z dallen $ */
// {{{ license

/*
 * Copyright 2002-2005 Dan Allen, Mojavelinux.com (dan.allen@mojavelinux.com)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// }}}
// {{{ intro

/**
 * Title: alphaAPI
 * Original Author: chrisken
 * Original Url: http://www.cs.utexas.edu/users/chrisken/alphaapi.html
 *
 * Modified by Dan Allen <dan.allen@mojavelinux.com>
 * Note: When the stopAlpha is reached and it is equal to 0, the element's
 * style is set to display: none to fix a bug in domTT
 */

// }}}
function alphaAPI(element, fadeInDelay, fadeOutDelay, startAlpha, stopAlpha, offsetTime, deltaAlpha)
{
	// {{{ properties

	this.element = typeof(element) == 'object' ? element : document.getElementById(element);
	this.fadeInDelay = fadeInDelay || 40;
	this.fadeOutDelay = fadeOutDelay || this.fadeInDelay;
	this.startAlpha = startAlpha;
	this.stopAlpha = stopAlpha;
	// make sure a filter exists so an error is not thrown
	if (typeof(this.element.filters) == 'object')
	{
		if (typeof(this.element.filters.alpha) == 'undefined')
		{
			this.element.style.filter += 'alpha(opacity=100)';
		}
	}

	this.offsetTime = (offsetTime || 0) * 1000;
	this.deltaAlpha = deltaAlpha || 10;
	this.timer = null;
	this.paused = false;
	this.started = false;
	this.cycle = false;
	this.command = function() {};
    return this;

	// }}}
}

// use prototype methods to save memory
// {{{ repeat()

alphaAPI.prototype.repeat = function(repeat)
{
    this.cycle = repeat ? true : false;
}

// }}}
// {{{ setAlphaBy()

alphaAPI.prototype.setAlphaBy = function(deltaAlpha)
{
    this.setAlpha(this.getAlpha() + deltaAlpha);
}

// }}}
// {{{ toggle()

alphaAPI.prototype.toggle = function()
{
    if (!this.started)
    {
        this.start();
    }
    else if (this.paused)
    {
        this.unpause();
    }
    else
    {
        this.pause();
    }
}

// }}}
// {{{ timeout()

alphaAPI.prototype.timeout = function(command, delay)
{
    this.command = command;
    this.timer = setTimeout(command, delay);
}

// }}}
// {{{ setAlpha()

alphaAPI.prototype.setAlpha = function(opacity)
{
    if (typeof(this.element.filters) == 'object')
    {
        this.element.filters.alpha.opacity = opacity;
    }
    else if (this.element.style.setProperty)
    {
        this.element.style.setProperty('opacity', opacity / 100, '');
		// handle the case of mozilla < 1.7
        this.element.style.setProperty('-moz-opacity', opacity / 100, '');
		// handle the case of old kthml
        this.element.style.setProperty('-khtml-opacity', opacity / 100, '');
    }
}	

// }}}
// {{{ getAlpha()

alphaAPI.prototype.getAlpha = function()
{
    if (typeof(this.element.filters) == 'object')
    {
        return this.element.filters.alpha.opacity;
    }
    else if (this.element.style.getPropertyValue)
    {
		var opacityValue = this.element.style.getPropertyValue('opacity');
		// handle the case of mozilla < 1.7
		if (opacityValue == '')
		{
			opacityValue = this.element.style.getPropertyValue('-moz-opacity');
		}

		// handle the case of old khtml
		if (opacityValue == '')
		{
			opacityValue = this.element.style.getPropertyValue('-khtml-opacity');
		}

        return opacityValue * 100;
    }

    return 100;
}

// }}}
// {{{ start()

alphaAPI.prototype.start = function()
{
    this.started = true;
    this.setAlpha(this.startAlpha);
    // determine direction
    if (this.startAlpha > this.stopAlpha)
    {
        var instance = this;
        this.timeout(function() { instance.fadeOut(); }, this.offsetTime);
    }
    else
    {
        var instance = this;
        this.timeout(function() { instance.fadeIn(); }, this.offsetTime);
    }
}

// }}}
// {{{ stop()

alphaAPI.prototype.stop = function()
{
    this.started = false;
    this.setAlpha(this.stopAlpha);
	if (this.stopAlpha == 0)
	{
		this.element.style.display = 'none';
	}

    this.stopTimer();
    this.command = function() {};
}

// }}}
// {{{ reset()

alphaAPI.prototype.reset = function()
{
    this.started = false;
    this.setAlpha(this.startAlpha);
    this.stopTimer();
    this.command = function() {};
}

// }}}
// {{{ pause()

alphaAPI.prototype.pause = function()
{
    this.paused = true;
    this.stopTimer();
}

// }}}
// {{{ unpause()

alphaAPI.prototype.unpause = function()
{
    this.paused = false;
    if (!this.started)
    { 
        this.start();
    }
    else
    {
        this.command(); 
    }
}

// }}}
// {{{ stopTimer()

alphaAPI.prototype.stopTimer = function()
{
    clearTimeout(this.timer);
    this.timer = null;
}

// }}}
// {{{ fadeOut()

alphaAPI.prototype.fadeOut = function()
{
    this.stopTimer();
    if (this.getAlpha() > this.stopAlpha)
    {
        this.setAlphaBy(-1 * this.deltaAlpha);
        var instance = this;
        this.timeout(function() { instance.fadeOut(); }, this.fadeOutDelay);
    }
    else
    {
        if (this.cycle)
        {
            var instance = this;
            this.timeout(function() { instance.fadeIn(); }, this.fadeInDelay);
        }
        else
        {
			if (this.stopAlpha == 0)
			{
				this.element.style.display = 'none';
			}
            this.started = false;
        }
    }
}

// }}}
// {{{ fadeIn()

alphaAPI.prototype.fadeIn = function()
{
    this.stopTimer();
    if (this.getAlpha() < this.startAlpha)
    {
        this.setAlphaBy(this.deltaAlpha);
        var instance = this;
        this.timeout(function() { instance.fadeIn(); }, this.fadeInDelay);
    }
    else
    {
        if (this.cycle)
        {
            var instance = this;
            this.timeout(function() { instance.fadeOut(); }, this.fadeOutDelay);
        }
        else
        {
            this.started = false;
        }
    }
}

// }}}
