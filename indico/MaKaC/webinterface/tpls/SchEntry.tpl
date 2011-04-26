<tr bgcolor="white">
    <td>${ nr }<td>
    <td align="center">${ moveUpButton }${ moveDownButton }</td>
    <td><b><font size="+2">${ description }</font></b></td>
    <td><form action="${ moveItemURL }" method="POST">
            ${ entryLocator }
            move <select name="after">
                    <option value="1" selected> ${ _("after")}</option>
                    <option value="0"> ${ _("before")}</option>
                 </select>
                 <select name="refEntry">${ refEntriesItems }</select>
                 <input type="submit" class="btn" value="${ _("do it")}">
        </form>
    </td>
</tr>
