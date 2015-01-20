<div class="container" style="margin: 50px auto; max-width: 420px">

    <div class="groupTitle" style="margin-bottom: 30px; font-size: 25pt; white-space: nowrap;">${ _("Reset your Indico password")}</div>

    <form action="" method="POST">
        <table style="border: 1px solid #DDDDDD; padding: 20px; border-radius:6px">
            <tr>
                <td class="titleCellTD">
                    <span class="titleCellFormat">${ _("Name")}</span>
                </td>
                <td class="contentCellTD" id="usernameInput">
                    <input type="text" name="_name" style="width: 99%;" value="${ rh._avatar.getStraightFullName() }" disabled>
                </td>
            </tr>
            <tr>
                <td class="titleCellTD">
                    <span class="titleCellFormat">${ _("Login")}</span>
                </td>
                <td class="contentCellTD" id="usernameInput">
                    <input type="text" name="_login" style="width: 99%;" value="${ rh._data['login'] }" disabled>
                </td>
            </tr>
            <tr>
                <td class="titleCellTD">
                    <span class="titleCellFormat" style="white-space: nowrap;">${ _("New Password")}</span>
                </td>
                <td class="contentCellTD" id="passwordInput">
                    <input type="password" name="password" style="width: 99%;">
                </td>
            </tr>
            <tr>
                <td class="titleCellTD">
                    <span class="titleCellFormat" style="white-space: nowrap;">${ _("Repeat password")}</span>
                </td>
                <td class="contentCellTD" id="passwordInput">
                    <input type="password" name="password_confirm" style="width: 99%;">
                </td>
            </tr>

            <tr>
                <td class="titleCellTD">&nbsp;</td>
                <td class="contentCellTD">
                    <div class="i-buttons">
                        <input type="submit" class="i-button right" value="${ _("Change password")}">
                    </div>
                </td>
            </tr>
        </table>
    </form>
</div>
