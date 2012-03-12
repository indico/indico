<%page args="hook"/>
<script type="text/javascript">
var pkBaseURL = (("https:" == document.location.protocol) ? "https://" : "http://")
pkBaseURL += '${ hook.url }';

document.write(unescape("%3Cscript src='" + pkBaseURL + "piwik.js' type='text/javascript'%3E%3C/script%3E"));
</script>
<script type="text/javascript">
try {

var piwikTracker = Piwik.getTracker(pkBaseURL + "piwik.php", 1);
% if hook.hasConfId:
piwikTracker.setCustomVariable(1, '${ hook.varConference }', '${ hook.confId }', 'page');
% endif
% if hook.hasContribId:
piwikTracker.setCustomVariable(2, '${ hook.varContribution }', '${ hook.contribId }', 'page');
% endif
piwikTracker.trackPageView();
piwikTracker.enableLinkTracking();
}
catch( err ) {}
</script>