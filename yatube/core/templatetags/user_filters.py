from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={'class': css})


@register.filter
def action_dict(calling_tag, form_name):
    user_form_dict = {
        'logout': (
            'Выход',
            'Вы вышли из своей учётной записи. Ждём вас снова!',
            ''),

        'login': (
            'Авторизация',
            '',
            'Войти'),

        'password_change_done': (
            'Изменение пароля',
            'Пароль изменён успешно',
            ''),

        'password_change_form': (
            'Изменить пароль',
            '',
            'Изменить пароль'),

        'password_reset_form': (
            'Сброс пароля',
            '',
            'Сбросить пароль'),

        'password_reset_done': (
            'Отправлено письмо',
            'Проверьте свою почту, вам должно прийти письмо со ссылкой для '
            'восстановления пароля',
            ''),

        'password_reset_complete': (
            'Восстановление пароля завершено',
            'Ваш пароль был сохранен. Используйте его для входа',
            ''),

        'password_reset_confirm_ok': (
            'Введите новый пароль',
            '',
            'Назначить новый пароль'),

        'password_reset_confirm_error': (
            'Ошибка',
            'Ссылка сброса пароля содержит ошибку или устарела.',
            ''),

        'password_reset_confirm_form': (
            'Сброс пароля',
            '',

            'Сбросить пароль',),

        'signup': (
            'Зарегистрироваться',
            '',
            'Зарегистрироваться'),

        'create_post': (
            'Новый пост',
            '',
            'Сохранить'),

        'edit_post': (
            'Редактировать пост',
            '',
            'Добавить')
    }

    if form_name in user_form_dict:
        if calling_tag == 'card_header':
            return user_form_dict[form_name][0]
        elif calling_tag == 'card_body':
            return user_form_dict[form_name][1]
        elif calling_tag == 'button_caption':
            return user_form_dict[form_name][2]
        else:
            return 'Action'
