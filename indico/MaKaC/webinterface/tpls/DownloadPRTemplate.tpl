<table cellspacing="0" align="center" width="100%" style="padding-top: 15px;">
   <tr>
       <td colspan="3"><div class="groupTitle">${ _("List of contribution templates")}</div></td>
   </tr>

   % if hasPaperReviewing: 
       ${ ContributionReviewingTemplatesList }
   % else: 
   <tr>
      <td nowrap class="displayField" style="padding-top: 5px; padding-left: 10px;">
            ${ _("There is no paper reviewing for this conference.")}
      </td>
   </tr>
   % endif
</table>


