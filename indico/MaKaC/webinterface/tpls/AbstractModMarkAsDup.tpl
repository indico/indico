<div class="groupTitle">${ _("Marking an abstract as a duplicate")}</div>

% if error:
  <div class="errorMessage">${error}</div>
% endif


<table>
    <tr>
        <td>
            <table>
                <tr>
                    <form action=${ duplicateURL } method="POST">
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Comments")}</span></td>
                    <td>&nbsp;
                        <textarea name="comments" rows="6" cols="50">${ comments }</textarea>
                    </td>
                </tr>
                <tr>
                    <td colspan="2"><br></td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Original abstract id")}</span></td>
                    <td>&nbsp;
                        <input type="text" name="id" value=${ id }>
                    </td>
                </tr>
            </table>
            <br>
        </td>
    </tr>
    <tr>
        <td align="left">
            <table align="left">
                <tr>
                    <td align="left">
                        <input type="submit" class="btn" name="OK" value="${ _("confirm")}">
                    </td>
                    </form>
                    <form action=${ cancelURL } method="POST">
                    <td align="left">
                        <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>
