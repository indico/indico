<%page args="target=None, shortResult=None"/>
<div style="overflow: auto; text-align: center;">
  % if page != 1:
  <span style="align: right;"><a href="#" onclick="$E('PrevForm${ target }').dom.submit(); return false;" style="margin-right: 10px;">< Previous</a></span>
  % endif

  <span style="align: center;"> Page ${ page } </span>

  % if not shortResult:
    <span style="align: right;"><a href="#" onclick="$E('NextForm${ target }').dom.submit(); return false;" style="margin-left: 10px;">Next ></a></span>
  % endif
</div>
