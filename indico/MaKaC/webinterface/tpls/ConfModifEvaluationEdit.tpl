
<!--ConfModifEvaluationEdit start-->
<table style="border-spacing:0px; width:90%%">  
  <tr>
    <td style="width: 125px;">
    
      <br/><br/>
    
      <!--left menu start-->
      <table class="evalEditLeftMenu">
        <tr>
          <th class="groupTitle"><%= _("New Question")%></th>
        <tr>
        <tr><td>
          <!--button Textbox-->
          %(form_tbox)s
        </td></tr>
        <tr><td>
          <!--button Textarea-->
          %(form_area)s
        </td></tr>
        <tr><td>
          <!--button Password-->
          %(form_pswd)s
        </td></tr>
        <tr><td>
          <!--button Select-->
          %(form_slct)s
        </td></tr>
        <tr><td>
          <!--button Radio-->
          %(form_radi)s
        </td></tr>
        <tr><td>
          <!--button Checkbox-->
          %(form_chck)s
        </td></tr>
      </table>
      <br/>
      <!--left menu end-->
      
    </td>
    <td style="margin-right:0px;padding-right:0px;border-spacing:0px;">
    
      <!--MAIN starts-->
      %(main)s
      <!--MAIN ends-->
      
    </td>
  </tr>
</table>
<!--ConfModifEvaluationEdit end-->
