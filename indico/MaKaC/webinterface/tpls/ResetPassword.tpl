<div class="container" style="width: 100%; margin: 50px auto; max-width: 600px">

    <div class="groupTitle" style="margin-bottom: 30px; font-size: 25pt;">${ _("Reset your Indico password")}</div>

    <form action="" method="POST">
        <table style="border: 1px solid #DDDDDD; padding: 20px; margin:auto; width:80%; border-radius:6px">
            <tr>
                <td class="titleCellTD">
                    <span class="titleCellFormat">${ _("Name")}</span>
                </td>
                <td class="contentCellTD" id="usernameInput">
                    <input type="text" name="_name" size="50" value="${ rh._avatar.getStraightFullName() }" disabled>
                </td>
            </tr>
            <tr>
                <td class="titleCellTD">
                    <span class="titleCellFormat">${ _("Login")}</span>
                </td>
                <td class="contentCellTD" id="usernameInput">
                    <input type="text" name="_login" size="50" value="${ rh._data['login'] }" disabled>
                </td>
            </tr>
            <tr>
                <td class="titleCellTD">
                    <span class="titleCellFormat">${ _("Password")}</span>
                </td>
                <td class="contentCellTD" id="passwordInput">
                    <input type="password" name="password" size="50">
                </td>
            </tr>
            <tr>
                <td class="titleCellTD">
                    <span class="titleCellFormat">${ _("Repeat password")}</span>
                </td>
                <td class="contentCellTD" id="passwordInput">
                    <input type="password" name="password_confirm" size="50">
                </td>
            </tr>

            <tr>
                <td class="titleCellTD">&nbsp;</td>
                <td class="contentCellTD">
                    <div class="yellowButton loginButton">
                        <input type="submit" value="${ _("Change password")}">
                    </div>
                </td>
            </tr>
        </table>
    </form>
</div>
