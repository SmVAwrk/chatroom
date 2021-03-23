"""
Переопределение функции create_user
(src: social_core.pipeline.user.create_user)
для нормальной работы с кастомной моделью пользователя.
В данной модели пользователя поле 'username' не определено,
вместо него в качестве основного используется 'email'.
Если провайдер oauth не предоставляет email, то в модель добавляется значение,
генерируемое на основе username и провайдера.
"""

import logging

USER_FIELDS = ['username', 'email']

logger = logging.getLogger(__name__)


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    fields = dict((name, kwargs.get(name, details.get(name)))
                  for name in backend.setting('USER_FIELDS', USER_FIELDS))

    # Генерация email, в случае его отсутствия
    if not fields.get('email', None):
        fields['email'] = fields['username'].lower() + '@' + backend.name + '.oauth'
        logger.debug(f'Генерация email на основе username - {fields["email"]}')

    return {
        'is_new': True,
        'user': strategy.create_user(**fields)
    }
