                    <select id="select_roomNameList" name="locationRoom">
                        <option value="">-------------------</option>
                        % for r in roomList:

                            <% selected = "" %>
                            % if r.name == locationRoom:
                                <% selected = 'selected' %>
                            % endif

                            <option value="${ r.name }" ${ selected } class="${roomClass( r )}">${ r.locationName + ": &nbsp; " + r.name }</option>
                        % endfor


                    </select>
