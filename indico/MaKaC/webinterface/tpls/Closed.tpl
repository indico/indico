<div class="toolsContainer" style="overflow: auto;">
       <div class="icon-locked icon-background inline-vcentered"></div>
       <div class="confirmation-dialog inline-vcentered">
           <form action="${postURL}" method="POST">
              <div class="body">
               <div>${message}</div>
               </div>
              % if showUnlockButton:
              <div class="buttons">
                <input type="submit" class="button accept" value="${ unlockButtonCaption }"/>
              </div>
              % endif
           </form>
       </div>
</div>

