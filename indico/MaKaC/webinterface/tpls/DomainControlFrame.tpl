<table class="groupTable">
<tr>
  <td colspan="2"><div class="groupTitle">${ _("Domain control ")}</div></td>
</tr>
</table>
<div>${ locator }</div>
<div class="domain_control">
  <div id="message"></div>
  <ul>
  % for dom, state in domains:
    <li>
      <input type="checkbox" name="selectedDomain" value="${dom.getId()}" ${'checked="checked"' if state else ''}>
        ${dom.getName()}
      </input>
    </li>
  % endfor
  </ul>
</div>
<script type="text/javascript">
function smooth_slide(el, text) {
    el.slideUp(function() {
        $(this).html(text)
    }).slideDown();
}

function refresh_state() {
    var el = $('.domain_control #message');

    var new_state = $(':checkbox:checked').length > 0;

    if (new_state == el.data('enabled')) {
        return;
    } else if (new_state){
        el.data('enabled', true);
        smooth_slide(el, $T('<span class="protPrivate strong">Access restricted</span><p>Only users in the networks selected below will be able to access this event.</p>'));
    } else{
        el.data('enabled', false);
        smooth_slide(el, $T('<span class="protPublic strong">Accessible from everywhere</span><p>To restrict access to this event only to certain IP addresses, choose at least one of the networks below.</p>'));
    }
}

$(function(){
    refresh_state();
});

$('input:checkbox').live('change', function(){
    $this = $(this);
    indicoRequest('event.protection.toggleDomains',
                  {
                      confId: ${conference.getId()},
                      domainId: $this.val(),
                      add: $this.is(':checked')
                  },
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
