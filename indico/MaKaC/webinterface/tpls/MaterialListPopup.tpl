<%page args="materials"/>

<ul class="material_list" style="display:none;">
  % for material in materials:
    <li class="section">
      <h3 class="name">${material['title']}</h3>
      <ul class="subPopupList">
        % for resource in material['resources']:
          <li><a class="fakeLink" href="${resource['url']}">${resource['name'] if resource['name'] else resource['url']}</a></li>
        % endfor
      </ul>
    </li>
  % endfor
</ul>
