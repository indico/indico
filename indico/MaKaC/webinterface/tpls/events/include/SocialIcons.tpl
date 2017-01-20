<%page args="dark, url, icalURL, "/>
<div id="fb-root"></div>

<div id="social_share">
  <h3>${_('Share this page')}</h3>
  <label for="direct_link">${_('Direct link:')}</label>
  <input id="direct_link" type="text" value="${url}" readonly/>
  <div class="note">${_('Please use <strong>CTRL + C</strong> to copy this URL')}</div>
  <div>
    <h4>${_('Social networks')}</h4>
    <div class="social_site">
      <span id="fb-loading">${_("Loading...")}</span>
      <fb:like id="fb-like" send="false" layout="standard" width="100" show-faces="false" colorscheme="${'dark' if dark else 'light'}" font="verdana"></fb:like>
    </div>
    <div class="social_site">
      <g:plusone size="medium"></g:plusone>
    </div>
    <div class="social_site">
      <a href="https://twitter.com/share" class="twitter-share-button" data-count="horizontal">${_("Tweet")}</a>
    </div>
  </div>
  <div>
    <h4>${_('Calendaring')}</h4>
  </div>
  <div class="social_site">
    <a href="http://www.google.com/calendar/event?${gc_params}" target="_blank"><img src="//www.google.com/calendar/images/ext/gc_button1.gif" alt="0" border="0"></a>
  </div>
</div>

<div id="social" data-url="${url}" data-theme="${'dark' if dark else 'light'}" data-social-settings="${social_settings|n,j,h}">
  <img src="${systemIcon('social.png')}" alt="${_("Social Networks")}"
       title="${_("Social Networks")}" id="social_button"/>
</div>
