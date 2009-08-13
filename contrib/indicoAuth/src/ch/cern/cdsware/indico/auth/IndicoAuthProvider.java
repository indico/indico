package ch.cern.cdsware.indico.auth;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLConnection;
import java.util.HashMap;
import java.util.Map;

import org.jivesoftware.openfire.auth.AuthProvider;
import org.jivesoftware.openfire.auth.ConnectionException;
import org.jivesoftware.openfire.auth.InternalUnauthenticatedException;
import org.jivesoftware.openfire.auth.UnauthorizedException;
import org.jivesoftware.openfire.user.UserNotFoundException;
import org.jivesoftware.util.JiveGlobals;
import org.jivesoftware.util.Log;
import org.json.JSONException;
import org.json.JSONObject;

public class IndicoAuthProvider implements AuthProvider {

	@Override
	public void authenticate(String username, String password)
			throws UnauthorizedException, ConnectionException,
			InternalUnauthenticatedException {

		Map<String, String> params = new HashMap<String, String>();
		params.put("username", username);
		params.put("digest", password);

		JSONObject obj = new JSONObject();
		try {
			obj.put("version", "1.1");
			obj.put("method", "messaging.authenticate");
			obj.put("params", params);
		} catch (Exception e1) {
			Log.error(e1);
		}

		try {

			String serviceURL = JiveGlobals.getProperty("indicoAuthProvider.jsonRpcEndpoint");
			if (serviceURL == null) {
				serviceURL = "http://localhost/services/json-rpc";
				Log.warn("You haven't specified a URL for the JSON-RPC endpoint - using " + serviceURL + " by default");
			}

			// add a property for this
			URL url = new URL(serviceURL);
			URLConnection connection = url.openConnection();
			connection.setDoOutput(true);

			OutputStreamWriter writer = new OutputStreamWriter(connection.getOutputStream());
			writer.write(obj.toString());
			writer.flush();

			BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));

			JSONObject returnObj = new JSONObject(reader.readLine());

			JSONObject error = null;
			if (returnObj.get("error") != JSONObject.NULL) {
				error = (JSONObject) returnObj.get("error");
			}

			System.out.println("error: " + error);

			String result = null;
			if (returnObj.get("result") != JSONObject.NULL) {
				result = returnObj.getString("result");
			}

			System.out.println("result: " + result);

			if (error != null) {
				Log.debug("Error: " + error.getString("message"));
				throw new ConnectionException("Error connecting: "+error.getString("message"));
			} else if (!result.toString().equals("OK")){
				Log.debug("NOTOK "+result);
				throw new UnauthorizedException();
			}

			Log.debug(returnObj.toString());

		} catch (MalformedURLException e) {
			Log.error(e);
		} catch (IOException e) {
			Log.error(e);
		} catch (JSONException e) {
			Log.error(e);
		}


	}

	@Override
	public void authenticate(String username, String token, String digest)
			throws UnauthorizedException, ConnectionException,
			InternalUnauthenticatedException {
		throw new UnsupportedOperationException();
	}

	@Override
	public String getPassword(String arg0) throws UserNotFoundException,
			UnsupportedOperationException {
		throw new UnsupportedOperationException();
	}

	@Override
	public boolean isDigestSupported() {
		return false;
	}

	@Override
	public boolean isPlainSupported() {
		return true;
	}

	@Override
	public void setPassword(String arg0, String arg1)
			throws UserNotFoundException, UnsupportedOperationException {
		throw new UnsupportedOperationException();
	}

	@Override
	public boolean supportsPasswordRetrieval() {
		return false;
	}
}
