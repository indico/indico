<table width="80%">
<tr>
  <td>
    <OBJECT id="VIDEO" width="480" height="430" // Player height = display size + 70 pixels of controls and status bar which cannot be removed, even though the ShowStatusBar is set to false
                CLASSID="CLSID:6BF52A52-394A-11d3-B153-00C04F79FAA6"
                type="application/x-oleobject">
                    <param name="url" value="${ url }">
                    <param name="AutoStart" value="true">
                    <param name="uiMode" value="Full">
                    <param name="ShowDisplay" value="false">
                    <param name="ShowStatusBar" value="false">

                    <embed
                    type="application/x-mplayer2"
                    pluginspage="http://www.microsoft.com/Windows/Downloads/Contents/MediaPlayer/"
                    width="480" height="403" src="${ url }" // Player height = display size + 43 pixels of controls
                    autostart="True"
                    showcontrols="True"
                    ShowStatusBar="false"
                    ShowDisplay="false">

                    </embed>
            </OBJECT>
  </td>
  <td><p>Playing Windows Media file...<br><a href="${ downloadurl }">Download file</a></p>
  </td>
</tr>
</table>

