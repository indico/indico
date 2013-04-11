<div class="conferenceDetails">
  <div itemprop="description" class="description ${'nohtml' if not description_html else ''}">${description}</div>

  <div class="grid">
  <div class="info_line date">
      <span  title="${_("Date/Time")}" class="icon icon-time" aria-hidden="true"></span>
      <div class="text">
        <div class="date_start">${_('Starts <span class="datetime">{0} {1}</span>').format(dateInterval[0], dateInterval[1])}</div>
        <div class="date_end">${_('Ends <span class="datetime">{0} {1}</span>').format(dateInterval[2], dateInterval[3])}</div>
        <div class="timezone">${timezone}</div>
      </div>
  </div>

  % if location:
    <div class="info_line location">
        <span title="${_("Location")}" class="icon icon-location" aria-hidden="true"></span>
        <div class="place text">
          ${location}
        </div>
      % if room:
        <div class="room text">${room}</div>
      % endif
      % if address:
        <div class="address text nohtml">${address}</div>
      % endif
    </div>
  % endif

  % if chairs:
  <div class="info_line chairs clear">
      <span  title="${_("Chairpersons")}" class="icon icon-chair" aria-hidden="true"></span>
      <ul class="chair_list text">
        % for chair in chairs:
        <li>
          % if chair.getEmail():
            % if self_._aw.getUser():
              <a href="mailto:${chair.getEmail()}">${chair.getFullName()}</a>
            % else:
              <a href="#" class="nomail">${chair.getFullName()}</a>
            % endif
          % else:
            ${chair.getFullName()}
          % endif
        </li>
        % endfor
      </ul>
  </div>
  % endif

  % if material:
  <div class="info_line material">
      <span title="${_("Materials")}" class="icon icon-material-download" aria-hidden="true"></span>
      % if isSubmitter:
        <span title="${_("Manage materials")}" class="right i-button icon-edit icon-only" id="manageMaterials" aria-hidden="true" ></span>
      % endif
      <ul class="text">
        % for mat in material:
          <li>${mat}</li>
        % endfor
      </ul>
  </div>
  % endif

  % if moreInfo:
  <div class="info_line info">
      <span  title="${_("Extra information")}" class="icon icon-info" aria-hidden="true"></span>
      <div class="text ${'nohtml' if not moreInfo_html else ''}">${ moreInfo }</div>
  </div>
  % endif
  </div>

</div>

${ actions }


<script type="text/javascript">
      $('.chair_list .nomail').qtip({
             content: {
                 text: $T("Login to see email address"),
             },
         });

% if isSubmitter:
    $('.info_line.material').css('background-color', '#eee');
    $("#manageMaterials").click(function(){
      IndicoUI.Dialogs.Material.editor(${conf.getId() |n,j}, '','','',
                                       ${conf.getAccessController().isProtected() |n,j},
                                       ${conf.getMaterialRegistry().getMaterialList(conf) |n,j},
                                       ${'Indico.Urls.UploadAction.conference'}, true);
    });

% endif

</script>
