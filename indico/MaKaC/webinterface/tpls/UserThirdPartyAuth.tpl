<% from indico.modules.oauth.db import Consumer, Token, ConsumerHolder, RequestTokenHolder %>
<% from indico.core.index import Catalog %>
<div class="groupTitle" id="userSection">${ _("Authorized Third Party Applications")}</div>

	<% request_tokens = Catalog.getIdx('user_oauth_request_token').get(user.getId()) %>
	% if request_tokens != None:
<div class="FavoritePeopleListDiv">
		<ul id="thirdPartyContainer" class="PeopleList">
		<% request_tokens = list(request_tokens) %>
		% for token in request_tokens:
			<li>
				<span>
					<div style="float: right; padding-right: 10px; padding-top: 5px; ">
						<a href="/indico/oauth.py/deauthorize_consumer?third_party_app=${token.getConsumer().getName()}&user_id=${user.getId()}"><img alt="Remove" title="Remove" src="http://pcuds43.cern.ch/indico/images/remove.png" style="margin-left: 5px; vertical-align: middle; ">
						</a>
					</div>
				</span>
				<span>
					${ token.getConsumer().getName() }
				</span>
			</li>
		% endfor
		</ul>
</div>
	% else:
		<h4>No third party application authorized yet.</h4>
	% endif