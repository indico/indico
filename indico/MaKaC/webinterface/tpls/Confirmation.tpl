<%page args="postURL, severity='warning', passingArgs={}, message={}, cancelButtonCaption=_('Cancel'), confirmButtonCaption=_('OK')"/>

<div class="confirmation-dialog">
  <h3 class="${severity}">
    ${ _("Confirmation Required")}
  </h3>

  <form id="confirmationForm" action="${postURL}" method="POST">

    <%block name="args">
      %for key, val in passingArgs.iteritems():
        %for value in (val if isinstance(val, list) else [val]):
          <input type="hidden" name="${key}" value="${value}" />
        %endfor
      %endfor
    </%block>

      <div class="body">
      % if isinstance(message, dict):
          <h3>
            <%block name="challenge">
              ${message['challenge']}
            </%block>
          </h3>
          <p class="target">
            <%block name="target">
              ${message['target']}
            </%block>
          </p>
            <div class="subtext">
              <%block name="subtext">
                % if message and message.get('subtext'):
                ${message['subtext']}
                % endif
              </%block>
            </div>
        </div>
        <div class="clearer"></div>
      % else:
       <div>${message}</div>
       </div>
      % endif
      <div class="i-buttons">
        <input type="submit" class="i-button right" name="cancel" value="${ cancelButtonCaption }"/>
        <input type="submit" class="i-button ${severity} right" name="confirm" value="${ confirmButtonCaption }"/>
      </div>
  </form>
</div>

<script type="text/javascript">

$('#confirmationForm > div > input').click(function() {
    if (${"true" if loading else "false"}) {
        if (this.name == "confirm"){
            var killLoadProgress = IndicoUI.Dialogs.Util.progress($T("Performing action..."));
        }
    }
})

</script>
