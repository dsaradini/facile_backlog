from django.conf import settings


def backlogman(request):
    my_dict = {
        'google_site_verify': settings.GOOGLE_SITE_VERIFY,
    }
    return my_dict
