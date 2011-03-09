<div id="layer1" class="marquee">
                      <table width="100%">
                        <tr>
                          <td align="center" width="100%"></td>
                        </tr>
                        <tr>
                          <td colspan="2"><marquee scrolldelay="2" scrollamount="<%= speed %>" onmouseover="this.stop();" onmouseout="this.start();">
						    <%= text %>
						  </td>
                        </tr>
                      </table>

                    </div>
                    <script type="text/javascript">
                    var y1 = 30;   // change the # on the left to adjuct the Y co-ordinate
                    (document.getElementById) ? dom = true : dom = false;
                    function placeIt() {
                        if (dom && !document.all) {
                           document.getElementById("layer1").style.bottom = -window.pageYOffset;
                           w=window.innerWidth-20;
                           document.getElementById("layer1").style.width=w-0;
                           document.getElementById("layer1").style.left = window.pageXOffset + ((window.innerWidth-w)/2);
                        }else if (document.layers) {
                           document.layers["layer1"].bottom = -window.pageYOffset;
                           w=window.innerWidth-40;
                           document.layers["layer1"].width = w-0;
                           document.layers["layer1"].left = window.pageXOffset + ((window.innerWidth-w)/2);
                        }else if (document.all) {
                           document.all["layer1"].style.top =document.body.scrollTop+document.body.clientHeight-document.all["layer1"].offsetHeight;
                           w=document.body.clientWidth-30;
                           document.all["layer1"].style.width = w;
                           document.all["layer1"].style.left = document.body.scrollLeft + ((document.body.clientWidth-w)/2);
                        }else{
                           document.getElementById("layer1").style.bottom = -window.pageYOffset;
                           w=window.innerWidth-20;
                           document.getElementById("layer1").style.width=w-0;
                           document.getElementById("layer1").style.left = window.pageXOffset + ((window.innerWidth-w)/2);
                        }
                        window.setTimeout("placeIt()", 10);
                    }
                    placeIt()
                    </script>