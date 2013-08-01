<%inherit file="Confirmation.tpl"/>

<%block name="args">
  %for contrib in contribList:
    <input type="hidden" name="selectedCateg" value="${contrib.getId()}" />
  %endfor
</%block>

<%block name="challenge">
  ${_("Are you sure that you want to delete the following contributions?")}
</%block>

<%block name="target">
  <ul>
  %for contrib in contribList:
    <li>${contrib.getTitle()}</li>
  %endfor
  </ul>
</%block>

<%block name="subtext">
  ${_("""Note that the following changes will result from this deletion:
<ul>
  <li>If the contribution is linked to an abstract</li>
    <ul>
      <li>The link between the abstract and the contribution will be deleted</li>
      <li>The status of the abstract will change to 'submitted'</li>
      <li>You'll lose the information about when and who accepted the abstract</li>
    </ul>
  </li>
</ul>
All the existing sub-contributions within the above contribution(s) will also be deleted
""")}
</%block>
