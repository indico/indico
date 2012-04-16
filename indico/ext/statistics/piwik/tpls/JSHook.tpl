<%page args="hook"/>
<script type="text/javascript">
var _paq = _paq || [];
(function(){
    var u=(("https:" == document.location.protocol) ? "https://" : "http://");
    u += '${ hook.url }';
    _paq.push(['setSiteId', ${ hook.siteId }]);
% if hook.hasConfId:
    _paq.push(['setCustomVariable', '1', '${ hook.varConference }', '${ hook.confId }', 'page']);
% endif
% if hook.hasContribId:
    _paq.push(['setCustomVariable', '2', '${ hook.varContribution }', '${ hook.contribId }', 'page']);
% endif
    _paq.push(['setTrackerUrl', u+'piwik.php']);
    _paq.push(['trackPageView']);
    _paq.push(['enableLinkTracking']);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0]; 
    g.type='text/javascript'; g.defer=true; g.async=true; g.src=u+'piwik.js';
s.parentNode.insertBefore(g,s); })();
</script>
