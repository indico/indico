import ZODB
import time
from urllib import urlencode
import urllib2
from random import choice
from string import ascii_letters, ascii_lowercase, digits
import oauth2 as oauth
from MaKaC.common.logger import Logger
from MaKaC.webinterface.rh import base
from MaKaC.webinterface import urlHandlers
from indico.core.index import Catalog
from MaKaC.webinterface.urlHandlers import UHThirdPartyAuth

from indico.modules.oauth.db import Consumer, Token, ConsumerHolder, AccessTokenHolder, RequestTokenHolder, TempRequestTokenHolder

REQUEST_TOKEN_URL = 'http://pcuds43.cern.ch/indico/oauth.py/request_token'
ACCESS_TOKEN_URL = 'http://pcuds43.cern.ch/indico/oauth.py/access_token'
AUTHORIZATION_URL = 'http://pcuds43.cern.ch/indico/oauth.py/authorize'
AUTHORIZE_CONSUMER_URL = 'http://pcuds43.cern.ch/indico/oauth.py/authorize_consumer'
DEAUTHORIZE_CONSUMER_URL = 'http://pcuds43.cern.ch/indico/oauth.py/deauthorize_consumer'
CALLBACK_URL = 'http://pcuds43.cern.ch/indico/oauth.py/request_token_ready'
RESOURCE_URL = 'http://pcuds43.cern.ch/indico/oauth.py/resource'
REALM = 'http://pcuds43.cern.ch/indico/'
VERIFIER = 'verifier'


#http://nullege.com/codes/show/src%40r%40e%40repoze-oauth-plugin-0.2%40repoze%40who%40plugins%40oauth%40plugin.py/45/oauth2.Server/python
def gen_random_string(length=40, alphabet=ascii_letters + digits):
    """Generate a random string of the given length and alphabet"""
    return ''.join([choice(alphabet) for i in xrange(length)])


class RHOAuth(base.RH):

    def __init__(self, req):
       base.RH.__init__(self, req)
       self.oauth_server = oauth.Server()
       self.oauth_server.add_signature_method(oauth.SignatureMethod_PLAINTEXT())
       self.oauth_server.add_signature_method(oauth.SignatureMethod_HMAC_SHA1())

   # example way to send an oauth error
    def send_oauth_error(self, err=None):
        # send a 401 error
        self._req.status = apache.HTTP_UNAUTHORIZED
        # return the authenticate header
        header = oauth.build_authenticate_header(realm=REALM)
        for k, v in header.iteritems():
            self._req.headers_out[k] = v

    def _checkParams(self, params):
        self._query_string = urlencode(params)

    def _process( self ):
        # debug info
        #print self.command, self.path, self.headers

        # get the post data (if any)
        postdata = None
        if self._req.get_method() == 'POST':
            try:
                length = int(self._req.headers_in.get('content-length'))
                postdata = self.rfile.read(length)
            except:
                pass


        # construct the oauth request from the request parameters
        oauth_request = oauth.Request.from_request(self._req.get_method(),
                                                self._req.construct_url(self._req.get_uri()), headers=self._req.headers_in,
                                                query_string=self._query_string)
        return self.process_req(oauth_request)


class RHOAuthRequestToken(RHOAuth):
    def process_req(self, oauth_request):
        # TODO: Consumer key registry (in ZODB) - key, secret for indico-mobile & others
        # TODO: Use consumer key to fetch associated Consumer identity from ZODB
        # TODO: Generate random key and secret, and store them in DB as request token for consumer
        # TODO: Save timestamp for request token
        # Token should have flag authorized=False
        # TODO: Return token key and secret (http://oauth.net/core/1.0/#anchor6)
        try:
            consumer_key = oauth_request.get_parameter('oauth_consumer_key')
            Logger.get('oauth.request_token').info(consumer_key)
            ZODB_consumer = ConsumerHolder().getById(consumer_key)
            Logger.get('oauth.request_token').info(ZODB_consumer.getSecret())
            consumer = oauth.Consumer(ZODB_consumer.getId(), ZODB_consumer.getSecret())
            self.oauth_server.verify_request(oauth_request, consumer, None)
            token = oauth.Token(gen_random_string(), gen_random_string())
            token.set_callback(oauth_request.get_parameter('oauth_callback'))
            timestamp = time.time()
            TempRequestTokenHolder().add(Token(token.key, token, timestamp, ZODB_consumer, None))
            # return the token

            Logger.get('oauth.request_token').info(token.to_string())
            return token.to_string()
        except oauth.Error, err:
            raise Exception(err)
            self.send_oauth_error(err)
        return


class RHOAuthAuthorization(RHOAuth, base.RHProtected):
    def process_req(self, oauth_request):
        try:
            user_id = self.getAW().getUser().getId()
            request_token_key = oauth_request.get_parameter('oauth_token')
            request_token = TempRequestTokenHolder().getById(request_token_key)
            verifier = gen_random_string()
            request_token.getToken().set_verifier(verifier)
            consumer = oauth.Consumer(request_token.getConsumer().getId(),
                request_token.getConsumer().getSecret())
            old_request_token = self._checkThirdPartyAuthPermissible(request_token.getConsumer().getName(), user_id)
            if old_request_token is not None:
                TempRequestTokenHolder().remove(request_token)
                request_token.setUserId(user_id)
                RequestTokenHolder().update(old_request_token, request_token)
                self._redirect(request_token.getToken().get_callback_url()+'&oauth_verifier='+verifier)
            else:
                TempRequestTokenHolder().remove(request_token)
                request_token.setUserId(user_id)
                RequestTokenHolder().add(request_token)
                redirectURL = '%s?user_id=%s&returnURL=%s&callback=%s&third_party_app=%s' %\
                    (UHThirdPartyAuth.getURL(),
                    user_id,
                    urllib2.quote(AUTHORIZE_CONSUMER_URL),
                    urllib2.quote(request_token.getToken().get_callback_url()),
                    urllib2.quote(request_token.getConsumer().getName()))
                self._redirect(redirectURL)
            return ''

        except oauth.Error, err:
            self.send_oauth_error(err)
        return

    def _checkParams(self, params):
        base.RHProtected._checkParams(self, params)
        RHOAuth._checkParams(self, params)

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _checkThirdPartyAuthPermissible(self, consumer, user_id):
        request_token = Catalog.getIdx('user_oauth_request_token').get(user_id)
        if request_token is not None:
            for token in list(request_token):
                if token.getConsumer().getName() == consumer:
                    return token
        return None


class RHOAuthAuthorizeConsumer(RHOAuth, base.RHProtected):
    def process_req(self, oauth_request):
        user_id = oauth_request.get_parameter('user_id')
        response = oauth_request.get_parameter('response')
        verifier = oauth_request.get_parameter('oauth_verifier')
        third_party_app = oauth_request.get_parameter('third_party_app')
        callback = oauth_request.get_parameter('callback')
        request_tokens = list(Catalog.getIdx('user_oauth_request_token').get(user_id))
        for request_token in request_tokens:
            if request_token.getToken().verifier == verifier:
                if response == 'accept':
                    self._redirect(callback+'&oauth_verifier='+verifier)
                else:
                    RequestTokenHolder().remove(request_token)
                    self._redirect(callback)


class RHOAuthDeauthorizeConsumer(RHOAuth, base.RHProtected):
    def process_req(self, oauth_request):
        user_id = oauth_request.get_parameter('user_id')
        third_party_app = oauth_request.get_parameter('third_party_app')
        request_tokens = Catalog.getIdx('user_oauth_request_token').get(user_id)
        access_tokens = Catalog.getIdx('user_oauth_access_token').get(user_id)
        if request_tokens:
            for token in list(request_tokens):
                if token.getConsumer().getName() == third_party_app:
                    RequestTokenHolder().remove(token)
        if access_tokens:
            for token in list(access_tokens):
                if token.getConsumer().getName() == third_party_app:
                    AccessTokenHolder().remove(token)
        self._redirect(urlHandlers.UHUserThirdPartyAuth.getURL())


class RHOAuthAccessTokenURL(RHOAuth):
    def process_req(self, oauth_request):
        # TODO: Fetch consumer from DB based on request token
        # Verify request
        # Generate access token and store it in DB, along with user id and current timestamp
        # Return token key, secret
        try:
            request_token_key = oauth_request.get_parameter('oauth_token')
            request_token = RequestTokenHolder().getById(request_token_key)
            consumer = oauth.Consumer(request_token.getConsumer().getId(), request_token.getConsumer().getSecret())
            self.oauth_server.verify_request(oauth_request, consumer, request_token.getToken())
            user_id = request_token.getUserId()
            access_tokens = Catalog.getIdx('user_oauth_access_token').get(user_id)
            timestamp = time.time()
            access_token_key = gen_random_string()
            access_token_secret = gen_random_string()
            if access_tokens is not None:
                for access_token in list(access_tokens):
                    if access_token.getConsumer().getName() == request_token.getConsumer().getName():
                        access_token.setTimestamp(timestamp)
                        response = {'oauth_token': access_token.getId(),
                        'oauth_token_secret': access_token.getToken().secret,
                        'user_id': user_id}
                        return urlencode(response)
            access_token = Token(access_token_key, oauth.Token(access_token_key, access_token_secret),
                timestamp, request_token.getConsumer(), user_id)
            AccessTokenHolder().add(access_token)
            response = {'oauth_token': access_token_key,
            'oauth_token_secret': access_token_secret,
            'user_id': user_id}
            return urlencode(response)
        except oauth.Error, err:
            self.send_oauth_error(err)
        return


class RHOAuthResourceURL(RHOAuth):
    def process_req(self, oauth_request):
        Logger.get('oauth.resource').info(oauth_request)
        return ''
        # Verify request
        # If access token is older than X, return http error 401
        try:
            # verify the request has been oauth authorized
            now = time.time()
            consumer_key = oauth_request.get_parameter('oauth_consumer_key')
            ZODB_consumer = ConsumerHolder().getById(consumer_key)
            token = oauth.Token.from_string(oauth_request.get_parameter('oauth_acces_token'))
            ZODB_access_token = AccessTokenHolder().getById(token.key, True)
            if not ZODB_access_token:
                raise oauth.Error('Wrong Access Token')
            elif (now - ZODB_access_token.getTimestamp()) > 10800:
                raise oauth.Error('Access Token has expired')
            else:
                params = self.oauth_server.verify_request(oauth_request)
                # return the extra parameters - just for something to return
                return str(params)
        except oauth.Error, err:
            self.send_oauth_error(err)
        return
