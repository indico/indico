function loginAs() {
    var popup = new ChooseUsersPopup(
        $T("Select user to log in as"), true, null, false,
        true, true, true, true,
        function(user) {
            indicoRequest(
                'admin.header.loginAs',
                {
                    userId: user[0]['id']
                },
                function(result, error) {
                    if (!error) {
                        // redirect to the same page
                        window.location.reload();
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
            );
        });
    popup.execute();
}
