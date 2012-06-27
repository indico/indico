$(function() {
    $('#click_me').click(function() {
        indicoRequest('hello.upper',
                      {
                          name: USER_NAME
                      }, function(result, error) {
                          alert("Server says: " + result);
                      })
    });

})