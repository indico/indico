<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <table cellspacing="0" align="center" width="100%" style="padding-top: 15px;">
       % if hasPaperReviewing:
       <tr>
           <table class="infoTable" cellspacing="0" width="100%">
           ${ ContributionReviewingTemplatesList }
           </table>
       </tr>
       % else:
       <tr>
          <td nowrap class="displayField" style="padding-top: 5px; padding-left: 10px;">
                ${ _("There is no paper reviewing for this conference.")}
          </td>
       </tr>
       % endif
    </table>
</%block>
