Indico.User = {
    id: {{ user.id | tojson }},
    first_name: {{ user.first_name | tojson }},
    last_name: {{ user.last_name | tojson }},
    favorite_users: {{ favorites | tojson }}
};
