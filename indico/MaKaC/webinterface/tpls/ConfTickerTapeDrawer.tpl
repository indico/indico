
% if nowHappeningArray:

<span class="nowHappeningText">${ _("Now happening:") }</span><div id="nowHappeningDiv" style="min-height: 20px;"></div>


<script type="text/javascript">
    var nowHappeningIndex = 0;
    var nowHappeningArray = ${ nowHappeningArray };
    var nowHappeningDiv = $E('nowHappeningDiv');
    var nowHappeningSpan = '';

    var nowHappeningRotateTime = 6000;
    var nowHappeningFadeTime = 350;

    var switchNowHappeningText = function() {
        nowHappeningDiv.dom.innerHTML = nowHappeningSpan + nowHappeningArray[nowHappeningIndex];
        // Fade in
        IndicoUI.Effect.fade($E('nowHappeningDiv'), nowHappeningFadeTime);
    }

    var rotateNowHappening = function() {
        // Fade out
        IndicoUI.Effect.fade($E('nowHappeningDiv'), nowHappeningFadeTime);

        setTimeout(switchNowHappeningText, nowHappeningFadeTime + 50);

        nowHappeningIndex++;
        if (nowHappeningIndex >= nowHappeningArray.length) {
            nowHappeningIndex = 0;
        }
        setTimeout(rotateNowHappening, nowHappeningRotateTime);
    };
    nowHappeningDiv.dom.innerHTML = nowHappeningSpan + nowHappeningArray[nowHappeningIndex];

    if (nowHappeningArray.length > 1)
        setTimeout(rotateNowHappening, nowHappeningRotateTime);

</script>

% endif

