<div class="center">
    <div class="confirmation-dialog">
        <h3 class="highlight text-left">
            ${ title }
        </h3>
        <div class="info-message-box">
            <div class="message-text">${ message }</div>
        </div>
        <div>
            <% anchor_tag = "<a href=\"{0}\">{1}</a>".format(url, link_text) %>
            ${ _("You will be automatically redirected to {0} in "
                 "<span id=\"timeleft\">{1}</span> seconds.").format(anchor_tag, str(delay)) }
            <br/>
            ${ _("Click <a href=\"{0}\">here</a> to go there now.".format(url)) }
        </div>
        <script>
        var delay = ${ delay };
        var timer = setInterval(function dcreaseDelay() {
            $('#timeleft').html('' + --delay);
            if (!delay) {
                clearInterval(timer);
                window.location.replace('${ url }');
            }
        }, 1000)
        </script>
    </div>
</div>
