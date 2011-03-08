
<form action=${ postURL } method="POST">
    <table width="65%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <tr>
            <td colspan="3" class="groupTitle"> ${ _("Creating a Booking on VRVS")}</td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><font color="red">*</font>  ${ _("Title")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="text" name="title" size="50" value="${ title }">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><font color="red">*</font>  ${ _("Description")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <textarea name="description" cols="43" rows="6">${ description }</textarea>
            </td>
        </tr>

        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Physical location")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
            <input type="text" name="locationRoom" value="${ locationRoom }"></td>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><font color="red">*</font>  ${ _("Start date")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <select name="sDay" onChange="this.form.eDay.value=this.value;">
                    ${ sday }
                </select>
                <select name="sMonth" onChange="this.form.eMonth.value=this.value;">
                    ${ smonth }
                </select>
                <select name="sYear" onChange="this.form.eYear.value=this.value;">
                    ${ syear }
                </select>
                <input type="image" src=${ calendarIconURL } alt="open calendar" border="0" onClick="javascript:window.open('${ calendarSelectURL }?daystring=sDay&monthstring=sMonth&yearstring=sYear&month='+this.form.sMonth.value+'&year='+this.form.sYear.value+'&date='+this.form.sDay.value+'-'+this.form.sMonth.value+'-'+this.form.sYear.value,'calendar','scrollbars=no,menubar=no,width=200,height=170');return false;">
                &nbsp;at&nbsp;
                <select name="sHour">
                  ${ shouroptions }
                </select>
                <select name="sMinute">
                  ${ sminuteoptions }
                </select>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><font color="red">*</font>  ${ _("End date")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <select name="eDay" onchange="">
                    ${ eday }
                </select>
                <select name="eMonth" onchange="">
                    ${ emonth }
                </select>
                <select name="eYear" onchange="">
                    ${ eyear }
                </select>
                <input type="image" src=${ calendarIconURL } alt="open calendar" border="0" onClick="javascript:window.open('${ calendarSelectURL }?daystring=eDay&monthstring=eMonth&yearstring=eYear&month='+this.form.eMonth.value+'&year='+this.form.eYear.value+'&date='+this.form.eDay.value+'-'+this.form.eMonth.value+'-'+this.form.eYear.value,'calendar','scrollbars=no,menubar=no,width=200,height=170');return false;">
                &nbsp;at&nbsp;
                <select name="eHour">
                    ${ ehouroptions }
                </select>
                <select name="eMinute">
                    ${ eminuteoptions }
                </select>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><font color="red">*</font>  ${ _("Email address or mailing list")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
            <input type="text" name="supportEmail" size="25" value="${ supportEmail }"></td>
        </tr>
        <tr>
     <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Protection password")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="text" name="accessPasswd" size="25" value="${ accessPasswd }">
            </td>
        </tr>
    <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Comments or remarks")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <textarea name="comments" cols="43" rows="4">${ comments }</textarea>
            </td>
        </tr>
    <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><font color="red">*</font>  ${ _("My VRVS user details")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <table>
                    <tr>
                        <td align="right"><small> ${ _("VRVS login")}</small></td>
                        <td align="left"><input type="text" name="vrvsLogin" value="${ vrvsLogin }"></td>
            <td align="right"><small>VRVS password</small></td>
            <td align="left"><input type="password" name="vrvsPasswd" value="${ vrvsPasswd }"></td>
            <td align="right"><small>Community Name</small></td>
            <td align="left"><select name="vrvsCommunity" value="${ vrvsCommunity }">
                                        <option value="" selected>---- ${ _("not selected")}----</option>
                                        <option value="Universe">Universe</option>
                                        <option value="HENP">HENP</option>
                                        <option value="AccessGrid">AccessGrid</option>
                                        <option value="ASTRO">ASTRO</option>
                                        <option value="Finland(FUNET)">FUNET (Finland)</option>
                                        <option value="France(RENATER)">RENATER (France)</option>
                                        <option value="FUSION">FUSION</option>
                                        <option value="GEANT2(DANTE)">DANTE (GEANT2)</option>
                                        <option value="GridCC">GridCC</option>
                                        <option value="ILC">ILC</option>
                                        <option value="Internet2">Internet2</option>
                                        <option value="Italy(INFN)">INFN (Italy)</option>
                                        <option value="MEDICAL">MEDICAL</option>
                                        <option value="PASCAL">PASCAL</option>
                                        <option value="Slovakia(SANET)">SANET (Slovakia)</option>
                                        <option value="Spain(RedIRIS)">RedIRIS (Spain)</option>
                                        <option value="UKERNA">UKERNA (UK)</option>
                                        <option value="VRVS_TEAM">VRVS Team</option>
                                        </td>
        </tr>
         </table>
            </td>
        </tr>

        <tr><td>&nbsp;</td></tr>
        <tr align="center">
            <td colspan="2" valign="bottom" align="center">
                <table align="center">
        <tr>
        <td><input type="submit" class="btn" value="${ _("Submit Booking")}"></td>
        <td><input type= "submit" class="btn" name="cancel" value= " ${ _("cancel")}"></td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr></tr>
        <tr><td></td><td align="left"><small> ${ _("Please note that the fields marked with * are compulsory and all the times are in your VRVS user timezone.")}</small></td></tr>
                </table>
        </tr>
</table>
</form>