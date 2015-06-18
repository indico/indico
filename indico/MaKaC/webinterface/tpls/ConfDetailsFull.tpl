<div class="conferenceDetails">
  <div itemprop="description" class="description ${'nohtml' if not description_html else ''}">${description}</div>

  <div class="infogrid">
  <div class="infoline date">
      <span  title="${_("Date/Time")}" class="icon icon-time" aria-hidden="true"></span>
      <div class="text">
        <div class="date_start">
            ${_('<span class="label">Starts</span> <span class="datetime">{0} {1}</span>').format(dateInterval[0], dateInterval[1])}
        </div>
        <div class="date_end">
            ${_('<span class="label">Ends</span> <span class="datetime">{0} {1}</span>').format(dateInterval[2], dateInterval[3])}
        </div>
        <div class="timezone">${timezone}</div>
      </div>
  </div>

  % if location:
    <div class="infoline location">
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
  <div class="infoline chairs clear">
      <span  title="${_("Chairpersons")}" class="icon icon-user-chairperson" aria-hidden="true"></span>
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

  % if material or isSubmitter:
  <div class="infoline material">
      <span title="${_("Materials")}" class="icon icon-package-download" aria-hidden="true"></span>
      % if material:
          <ul class="text" style="float: left; padding: 0">
            % for mat in material:
              <li>${mat}</li>
            % endfor
          </ul>
      % else:
          <span class="text" style="float: left; font-style: italic; padding: 10px 0px 0px">${_("No material yet")}</span>
      % endif

  </div>
  % endif

  % if moreInfo:
  <div class="infoline info">
      <span  title="${_("Extra information")}" class="icon icon-info" aria-hidden="true"></span>
      <div class="text ${'nohtml' if not moreInfo_html else ''}">${ moreInfo }</div>
  </div>
  % endif

  % if registration_enabled and in_registration_period or registrant:
    <div class="infoline registration">
        <span class="icon icon-ticket"></span>
        <div class="text">
            % if not registrant:
                <div class="label">
                    ${ _("Registration for this event is now open") }
                </div>
                <div>
                    ${ _("Deadline:") } <span class="date">${ registration_deadline }</span>
                </div>
            % else:
                <div class="label">
                    ${ _("You are registered for this event") }
                </div>
                <div>
                    % if registrant.doPay():
                        ${ _("Go to checkout to complete your registration") }
                    % elif in_modification_period:
                        ${ _("Modifications allowed until: ") } <span class="date">${ modification_deadline }</span>
                    % else:
                        ${ _("Go to summary to check your details") }
                    % endif
                </div>
            % endif
            <div class="toolbar right">
                % if not registrant:
                    <a href="${ url_for('event.confRegistrationFormDisplay-display', conf) }" class="i-button next highlight">
                        ${ _("Register now") }
                    </a>
                % else:
                    % if ticket_enabled:
                        <div class="group">
                            <a href="${ url_for('event.e-ticket-pdf', conf) }" class="i-button icon-ticket">
                                ${ _("Get ticket") }
                            </a>
                        </div>
                    % endif
                    <div class="group">
                        % if in_modification_period:
                            <a href="${ url_for('event.confRegistrationFormDisplay-modify', conf) }"class="i-button icon-edit">
                                ${ _('Modify') }
                            </a>
                        % endif
                        <a href="${ url_for('event.confRegistrationFormDisplay', conf) }" class="i-button next highlight">
                            % if registrant.doPay():
                                ${ _("Checkout") }
                            % else:
                                ${ _("Summary") }
                            % endif
                        </a>
                    </div>
                % endif
            </div>
        </div>
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
    $('.infoline.material').addClass('highlighted-area');
    $('.infoline.material').css('background-color', '#f2f2f2');
    $('.infoline.material').append('<span title="${_("Manage materials")}" class="right i-button icon-edit icon-only" style="float: right" id="manageMaterials" aria-hidden="true" ></span>');


    $("#manageMaterials").click(function(){
      IndicoUI.Dialogs.Material.editor(${conf.getOwner().getId() |n,j}, ${conf.getId() |n,j}, '','','',
                                       ${conf.getAccessController().isProtected() |n,j},
                                       ${conf.getMaterialRegistry().getMaterialList(conf) |n,j},
                                       ${'Indico.Urls.UploadAction.conference'}, true);
    });

% endif

</script>
