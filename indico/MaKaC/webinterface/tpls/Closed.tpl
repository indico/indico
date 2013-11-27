<div class="toolsContainer" style="overflow: auto;">
       <div class="icon-locked icon-background inline-vcentered"></div>
       <div class="confirmation-dialog inline-vcentered">
           <form action="${postURL}" method="POST">
              <div class="body">
               <div>${message}</div>
               </div>
              % if showUnlockButton:
              <div class="toolbar">
                <input type="submit" class="i-button accept" value="${ unlockButtonCaption }"/>
              </div>
              % endif
           </form>
       </div>
</div>

