from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication


@database_sync_to_async
def get_user_jwt(validated_token):
    try:
        return JWTTokenUserAuthentication().get_user(validated_token=validated_token)
    except Exception:
        return AnonymousUser()


@database_sync_to_async
def get_user_token(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Exception:
        return AnonymousUser()


class JWTOrTokenAuthMiddleware(BaseMiddleware):

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        try:
            query = dict((x.split('=') for x in scope['query_string'].decode().split('&')))
        except Exception as exc:
            print(exc)
        token_key = query.get('token')
        validated_token = JWTTokenUserAuthentication().get_validated_token(
            raw_token=token_key
        )
        scope['user'] = await get_user_jwt(validated_token)
        if isinstance(scope['user'], AnonymousUser):
            scope['user'] = await get_user_token(token_key)
        return await super().__call__(scope, receive, send)


def JWTOrTokenAuthMiddlewareStack(inner):
    return JWTOrTokenAuthMiddleware(AuthMiddlewareStack(inner))
