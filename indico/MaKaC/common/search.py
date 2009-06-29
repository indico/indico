from MaKaC.user import AvatarHolder, GroupHolder
from MaKaC.conference import ConferenceHolder

def searchPeople(surName="", name="", organisation="", email="", group="", conferenceId=None, exactMatch=True, searchExt=False):
    results = {}
    if surName != "" or name != "" or organisation != "" or email != "":
        # build criteria
        criteria = {
            "surName": surName,
            "name": name,
            "organisation": organisation,
            "email": email
        }
        # search users
        people = AvatarHolder().match(criteria, exact=exactMatch, forceWithoutExtAuth=(not searchExt))
        # search authors
        if conferenceId != None:
            try:
                conference = ConferenceHolder().getById(conferenceId)
                authorIndex = conference.getAuthorIndex()
                authors = authorIndex.match(criteria, exact=exactMatch)
                # merge with users
                users = people
                people = []
                emails = []
                for user in users:
                    people.append(user)
                    emails.extend(user.getEmails())
                for author in authors:
                    if author.getEmail() not in emails:
                        people.append(author)
            except:
                pass
        results["people"] = people
    if group != "":
        # build criteria
        criteria = {
            "name": group
        }
        # search groups
        groups = GroupHolder().match(criteria, forceWithoutExtAuth=(not searchExt))
        results["groups"] = groups
    return results
