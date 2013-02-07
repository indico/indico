<div class="toolsContainer">
       <div class="icon-locked icon-background"></div>
       <div class="confirmation-dialog">
           <form action="${postURL}" method="POST">
              <div class="body">
               <div>${message}</div>
               </div>
              % if showUnlockButton:
              <div class="buttons">
                <input type="submit" class="bs-btn accept" value="${ unlockButtonCaption }"/>
              </div>
              % endif
           </form>
       </div>
</div>

