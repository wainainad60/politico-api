from flask import request, Blueprint, current_app
from werkzeug.security import check_password_hash
from api.strings import post_method, status_201, id_key, status_404,\
    status_200, status_400, get_method
from api.ver1.utils import error, no_entry_resp, check_form_data, \
    field_missing_resp, success
from api.ver1.users.strings import *
from api.ver2.utils.strings import password_1, password_2, admin_key, \
    user_entity, token_key, user_key, password_key
from api.ver2.models.users import User
from api.ver2.models.auth import Auth
from api.ver2.utils.validators import is_valid_email, invalid_passwords
from api.ver2.utils.utilities import system_unavailable
from werkzeug.security import generate_password_hash
from api.ver2.utils import is_not_admin
from flask_jwt_extended import (jwt_required, get_jwt_identity)
import sendgrid
from sendgrid.helpers.mail import *
import traceback
import os

auth = Blueprint('auth', __name__)
reset_token = None
reset_user = None


@auth.route('/auth/signup', methods=[post_method])
def signup():
    try:
        fields = [fname, lname, email, pspt, phone, password_key]
        res_data = check_form_data(user_entity, request, fields)
        if res_data:
            try:
                user = User(
                    fname=res_data[fname],
                    lname=res_data[lname],
                    email=res_data[email],
                    passport_url=res_data[pspt],
                    phone=res_data[phone],
                    password=res_data[password_key],
                )
            except Exception as e:
                return field_missing_resp(user_entity, fields, e.args[0])

            if not user.validate_user():
                return error(user.message, user.code)
            user_auth = Auth(email=res_data[email],
                             password=res_data[password_key])
            if not user_auth.validate_auth():
                return error(user_auth.message, user_auth.code)
            user_auth.create()
            user.Id = user_auth.Id
            user.create()
            return success(status_201, [{
                token_key: user_auth.access_token,
                user_key: user.to_json()
            }])

        else:
            return no_entry_resp(user_entity, fields)
    except Exception as e:
        return system_unavailable(e)


@auth.route('/auth/login', methods=[post_method])
def login():
    try:
        fields = [email, password_key]
        res_data = check_form_data(user_key, request, fields)
        if res_data:
            try:
                code = None
                message = ''
                mail = res_data[email]
                password = res_data[password_key]
            except Exception as e:
                return field_missing_resp(user_entity, fields,
                                          e.args[0], 'login')
            login_user = Auth().get_by(email, mail)
            if not login_user:
                code = status_404
                message = "user does not exits in the database"
            elif not check_password_hash(login_user[password_key], password):
                code = status_400
                message = 'Incorrect password provided'
            else:
                user = Auth(Id=login_user[id_key], email=mail)
                user.create_auth_tokens()
                if login_user[admin_key]:
                    user_in4 = Auth().get_admin(email, mail)
                else:
                    user_in4 = User().get_by_id(login_user[id_key])
                code = status_200
                data = {
                    token_key: user.access_token,
                    user_key: user_in4
                }
                return success(code, [data])
            return error(message, code)
        else:
            return no_entry_resp(user_entity, fields)
    except Exception as e:
        return system_unavailable(e)


@auth.route('/auth/users', methods=[get_method])
@jwt_required
def users():
    if is_not_admin():
        return is_not_admin()
    try:
        return success(200, User().get_all())
    except Exception as e:
        return system_unavailable(e)


@auth.route('/auth/reset', methods=[post_method])
def reset():
    try:
        message = ''
        code = status_400
        fields = [email]
        data = check_form_data(user_key, request, fields)
        if data:
            try:
                data[email]
            except ValueError:
                message = 'Please provide an email to reset you password'
            try:
                mail = data[email]
                if is_valid_email(mail):
                    user = Auth().get_by(email, mail)
                    if user:
                        global reset_token, reset_user
                        res_user = Auth(Id=user['id'])
                        res_user.create_auth_tokens()
                        reset_token = res_user.access_token
                        reset_user = mail
                        res_data = [{
                            'message':
                                'Check your email for password reset link',
                            'email': mail,
                            'token': reset_token
                        }]
                        reset_url = \
                        """https://wainainad60.github.io/Politico/templates/reset_pass.html?token={}""".format(
                            reset_token)
                        code = status_200
                        print(reset_url)
                        sg = sendgrid.SendGridAPIClient(
                            apikey=os.environ.get('SENDGRID_API_KEY'))
                        with open('pass_reset_markup.html', 'r') as \
                                reset_markup:
                            text = reset_markup.read().replace('\n', '')
                            text = text.replace('action_url', reset_url)
                            try:
                                text = text.replace(
                                    'username',
                                    User().get_by_id(user['id'])['fname'])
                            except Exception:
                                return error('Admin Not Allowed To Reset '
                                             'Password!', 400)

                        from_email = Email("politico-noreply@politico.com")
                        to_email = Email(mail)
                        subject = "Password reset link"
                        content = Content("text/html",
                                          text)
                        try:
                            mail = Mail(from_email, subject, to_email, content)
                            response = sg.client.mail.send.post(
                                request_body=mail.get())
                            if response.status_code == 202:
                                return success(code, res_data)
                        except Exception as e:
                            system_unavailable(e)
                    else:
                        message = 'No user is registered with that email'
                        code = status_404
                else:
                    message = 'Please enter a valid email'
            except Exception as e:
                return error('runtime exception: {}, {}'.format(e.args[0],
                                traceback.print_exc()), 500)
        else:
            message = 'No Input Received: ' \
                      'Please input an email to reset you password'
        return error(message, code)
    except Exception as e:
        return system_unavailable(e)


@auth.route('/auth/reset/link/<string:token>', methods=[post_method])
@jwt_required
def reset_link(token):

    fields = [password_1, password_2]
    data = check_form_data(user_key, request, fields)
    if data:
        try:
            pass1 = data[password_1]
            pass2 = data[password_2]
            invalid = invalid_passwords(pass1, pass2)
            if not invalid:
                user = Auth().patch(
                    password_key,
                    generate_password_hash(pass1),
                    get_jwt_identity())
                del user['password']
                return success(
                    200, [
                        {'message': 'password reset successful, '
                                    'please login',
                         'user': user}])
            return error(invalid['message'], invalid['code'])
        except KeyError as e:
            return error(
                'Please provide a value for {} to reset you password'
                ''.format(e.args[0]),
                status_400
            )
    else:
        return error(
            'Please input New Password twice to reset '
            'current password. fields={}'.format(fields),
            status_400
        )

