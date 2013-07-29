<%page args="field=None, fdict=None"/>
<% from indico.MaKaC.review import AbstractTextField %>
<% from indico.MaKaC.review import AbstractTextAreaField %>
<% from indico.MaKaC.review import AbstractInputField %>
<% from indico.MaKaC.review import AbstractSelectionField %>

<% fid = "f_" + field.getId() %>
% if not field.isActive():
    <input type="hidden" name=${fid} value="">
% else:
    <tr>
        <td align="right" valign="top"  style="white-space:nowrap">
            <span class="dataCaptionFormat">
                ${field.getCaption()}
            </span>
            % if field.isMandatory():
                <span class="mandatoryField">*</span>
            % endif
            % if field.getType() == "textarea" or field.getType() == "input":
                <% nbRows = 10 %>
                % if field.getMaxLength() > 0:
                    % if field.getLimitation() == "words":
                        <% nbRows = int((int(field.getMaxLength())*4.5)/85) + 1 %>
                        <input type="hidden" name="maxwords${field.getId().replace(" ", "_")}" value="${field.getMaxLength()}">
                        <small>
                            <span id="maxLimitionCounter_${field.getId().replace(" ", "_")}" style="padding-right:5px;">
                                ${field.getMaxLength()} ${_(" words left")}
                            </span>
                        </small>
                    % else:
                        <% nbRows = int(int(field.getMaxLength())/85) + 1 %>
                        <input type="hidden" name="maxchars${field.getId().replace(" ", "_")}" value="${field.getMaxLength()}">
                        <small>
                            <span id="maxLimitionCounter_${field.getId().replace(" ", "_")}" style="padding-right:5px;">
                                ${field.getMaxLength()} ${_(" chars left")}
                            </span>
                        </small>
                    % endif
                % endif
                % if (nbRows > 30):
                    <% nbRows = 30 %>
                % endif
            % endif
        </td>
        <td>
            % if field.getType() == "textarea":
                <textarea id=${fid} name=${fid} width="100%" rows="${nbRows}" style="width:100%">${fdict[fid]}</textarea>
            % elif field.getType() == "input":
                <input id=${fid} name=${fid} value="${fdict[fid]}" style="width:100%">
            % elif field.getType() == "selection":
                <select id=${fid} name=${fid}>
                    <% nooption = "{}...".format(_("Choose")) %>
                    <% selected = "selected" if fdict[fid] == "" else "" %>
                    <option value="" disabled ${selected}>${nooption}</option>
                    % for option in field.getOptions():
                        <% selected = "selected" if fdict[fid] == option.getId() else "" %>
                        <option value="${option.getId()}" ${selected}>${option.getValue()}</option>
                    % endfor
                </select>
            % endif
        </td>
    </tr>
% endif
