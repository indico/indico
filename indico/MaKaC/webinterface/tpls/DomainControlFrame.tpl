<table class="groupTable">
<tr>
  <td colspan="2"><div class="groupTitle">${ _("Domain control ")}</div></td>
</tr>
</table>
<div>${ locator }</div>
<div class="domain_control" style="max-width: 600px;">
  % if inheriting:
    <div class="warning-message-box">
      <div class="message-text">
        ${_("This category is inheriting its domain access settings from its parent.")}
      </div>
    </div>
  % endif
  <div id="message"></div>
  <form autocomplete="off">
  <ul>
  % for dom, state in domains.iteritems():
    <li>
      <input type="checkbox" name="selectedDomain" value="${dom.getId()}" ${'checked' if state else ''}
    ${'disabled' if inheriting else ''}>
        ${dom.getName()}
      </input>
    </li>
  % endfor
  </ul>
  </form>
</div>

<script type="text/javascript">

function smooth_slide(el, text, immediately) {
    if (immediately) {
        el.html(text);
        return;
    }
    el.slideUp(function() {
        $(this).html(text)
    }).slideDown();
}

function refresh_state(immediately) {
    var el = $('.domain_control #message');

    var new_state = $(':checkbox:checked').length > 0;

    if (new_state == el.data('enabled')) {
        return;
    } else if (new_state){
        smooth_slide(el, $T('<span class="protPrivate strong">Access restricted</span><p>Only users in the networks selected below will be able to access this event.</p>'), immediately);
    } else{
        smooth_slide(el, $T('<span class="protPublic strong">Accessible from everywhere</span><p>To restrict access to this event only to certain IP addresses, choose at least one of the networks below.</p>'), immediately);
    }

    el.data('enabled', new_state);
}

$(function(){
    refresh_state(true);
});

$('.domain_control input:checkbox').on('change', function(){
   var $this = $(this);
   var params = {
                  targetId: '${target.getId()}',
                  domainId: $this.val(),
                  add: $this.is(':checked')
                };

   % if event is not None:
       params['confId'] = ${ event.getId() | n,j};
   % endif

    indicoRequest('${method}',
                  params,
                  function(result, error) {
                      if(error) {
                          IndicoUtil.errorReport(error);
                      } else{
                          // only create indicator if there is not already one
                          if (!$('.savedText', $this.closest('li')).length) {
                              var saved = $('<span class="savedText">saved</span>');
                              $this.closest('li').append(saved);
                              saved.delay(1000).fadeOut('slow', function() {
                                  $(this).remove();
                              });
                          }
                          refresh_state();
                      }
                  });
                 });
</script>
