<table class="groupTable">
<form action="${ createDomainURL }" method="GET">

<tr>
  <td colspan="2"><div class="groupTitle">${ _("Domain tools") }</div></td>
</tr>
<tr>
  <td></td>
  <td class="blacktext"><em>${ _("The database currently hosts") } ${ nbDomains } ${ _("domains.")}</em></td>
</tr>
<tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Tools")}</span></td>
    <td bgcolor="white" class="blacktext">
        <input type="submit" value="${ _("New Domain")}" class="btn">
    </td>
</tr>
</form>


<form action="${ browseDomainsURL }" method="POST" name="browseForm">
<input type="hidden" value="" name="letter">
<tr>
  <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Browse Domains")}</span></td>
  <td>${ browseDomains }</td>
</tr>
</form>


<form action="${ searchDomainsURL }" method="POST">
<tr>
    <td colspan="2"><div class="groupTitle">${ _("Search Domains") }</div></td>
    <td>
</tr>
<tr>
    <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Name")}</span></td>
    <td class="blacktext"><input type="text" name="sName"></td>
</tr>
<tr>
    <td>&nbsp;</td>
    <td><input type="submit" class="btn" value="${ _("apply")}"></input></td>
</tr>

<tr>
    <td>&nbsp;</td>
    <td>
        <table width="100%"><tbody>
            ${ domains }
        </tbody></table>
        <br /><br />
    </td>
</tr>
</form>
</table>
