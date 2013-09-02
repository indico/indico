<div>
  <form action="${statusURL}" method="POST">
    <span>${_("Current status:")}</span>
    <b>${ status }</b>
    <input name="changeTo" type="hidden" value="${changeTo}">
    <input type="submit" value="${ changeStatus }">
  </form>
</div>
