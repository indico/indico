<%inherit file="/search/SearchBoxBase.tpl"/>

<%block name="searchExtras">
    <tr>
    <td style="text-align: right;">${ _("Search for")}</td>
    <td>
        <select name="collections">
          <option value="Events">Events</option>
          <option value="Contributions">Contributions</option>
          <option value="" selected>Both (Events+Contributions)</option>
        </select>
    </td>
    </tr>
</%block>
