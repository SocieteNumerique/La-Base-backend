import functools

from main.factories import UserFactory


def authenticate(func):
    @functools.wraps(func)
    def authenticate_and_func(*args, **kwargs):
        authenticate.user = UserFactory.create()
        args[0].client.force_login(user=authenticate.user)
        return func(*args, **kwargs)

    return authenticate_and_func


def snake_to_camel_case(snake_case):
    if snake_case == "":
        return
    words = snake_case.split("_")
    return words[0] + "".join(word.title() for word in words[1:])
