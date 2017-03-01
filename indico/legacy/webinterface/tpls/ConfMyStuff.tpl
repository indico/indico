<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div>
    <table width='100%'>
        <tr>
               <td nowrap class="displayField" style="padding-top: 25px; padding-left: 10px;">
                  <b>
                     ${ _("This section gives you the opportunity to access all your features for this conference.")}
                  </b>
               </td>
        </tr>
        <tr>
               <td style="padding-left: 30px; padding-top: 10px">
                  <font color="gray"> ${ _("To navigate, please use the sublink(s) located under 'My Conference'.") }
                  </font>
               </td>
        </tr>
    </table>
    </div>
</%block>
