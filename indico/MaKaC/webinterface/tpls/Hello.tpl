<script type="text/javascript">
var USER_NAME = ${name | n,j}; // Get name in JSON format (escaped string)
</script>
<h1>Hello, ${name}!</h1>

<p>
Welcome to this Indico development walkthrough.
</p>

<ul>
  % for character_name in ["Lancelot", "Galahad", "Tim the Enchanter"]:
  <li>
    Say hello to <a href="${urlHandlers.UHHello.getURL(name=character_name)}">${character_name}</a>!
  </li>
  % endfor
</ul>

<button id="click_me">Click me!</button>
</p>