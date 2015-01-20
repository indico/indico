<div class="center">
    <div class="confirmation-dialog">
        <h3 class="highlight text-left">
            ${ title }
        </h3>
        <div class="info-message-box">
            <div class="message-text">${ message }</div>
        </div>
        <div>
            ${ _('You will be automatically redirected to <a href="{0}">{1}</a> in '
                 '<span id="timeleft">{2}</span> seconds.').format(url, link_text, delay) }
            <br/>
            ${ _('Click <a href="{0}">here</a> to go there now.').format(url) }
        </div>
        <script>
        var delay = ${ delay };
        var timer = setInterval(function decreaseDelay() {
            $('#timeleft').html('' + --delay);
            if (!delay) {
                clearInterval(timer);
            }
        }, 1000);
        </script>
    </div>
</div>
