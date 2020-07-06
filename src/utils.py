import requests


def is_url_image(url):
    """Return True if the url is an existing image."""
    img_formats = ('image/png', 'image/jpeg', 'image/jpg')
    return requests.head(url).headers["content-type"] in img_formats


def team_name(id_team):
    """Return the name of the team from its id."""
    return ('Nobody', 'Red', 'Blue')[id_team]
