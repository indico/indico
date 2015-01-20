<%page args="errors, msg"/>
% if errors:
    <div class="error-message-box">
        <div class="message-text">
            ${ msg }:
            <ul>
                % for error in errors:
                    <li>${ error }</li>
                % endfor
            </ul>
        </div>
    </div>
% endif
