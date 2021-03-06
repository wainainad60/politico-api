from flask import request, Blueprint
from flask_jwt_extended import (jwt_required)
from api.ver1.utils import field_missing_resp, runtime_error_resp, \
    not_found_resp, check_form_data, no_entry_resp, error, success
from api.strings import name_key, post_method, get_method, delete_method
from api.ver1.parties.strings import hqAddKey, logoUrlKey, party_key
from api.ver2.models.parties import Party
from api.ver2.utils import is_not_admin
from api.ver2.utils.utilities import system_unavailable
from api.ver2.utils.validators import invalid_name

party_v2 = Blueprint('parties_v2', __name__)


@party_v2.route('/parties', methods=[post_method, get_method])
@jwt_required
def add_or_get_all_ep():
    try:
        if request.method == post_method:
            """ create party endpoint """
            if is_not_admin():
                return is_not_admin()
            fields = [name_key, hqAddKey, logoUrlKey]
            data = check_form_data(party_key, request, fields)
            if not data:
                return no_entry_resp(party_key, fields)
            try:
                name = data[name_key]
                hq_address = data[hqAddKey]
                logo_url = data[logoUrlKey]
                party = Party(name=name, hqAddress=hq_address, logoUrl=logo_url)
                if party.validate_party():
                    party.create()
                    return success(201, [party.to_json()])
                else:
                    return error(party.message, party.code)
            except KeyError as e:
                return field_missing_resp(party_key, fields, e.args[0])

        elif request.method == get_method:
            data = []
            parties = Party().get_all()
            for party in parties:
                data.append(party)
            return success(200, data)
    except Exception as e:
            return system_unavailable(e)


@party_v2.route('/parties/<int:id>', methods=[delete_method, get_method])
@jwt_required
def get_or_delete_ep(id):
    try:
        party = Party(Id=id)
        if party.get_by('id', id):
            p = party.get_by('id', id)
            if request.method == get_method:
                return success(200, [p])
            elif request.method == delete_method:
                if is_not_admin():
                    return is_not_admin()
                party.delete(id)
                return success(200, [{'message': p['name']
                                                 + ' deleted successfully'}])
        else:
            return not_found_resp(party_key)
    except Exception as e:
        return system_unavailable(e)


@party_v2.route('/parties/<int:id>/name', methods=['PATCH'])
@jwt_required
def edit_ep(id):
    try:
        if is_not_admin():
            return is_not_admin()
        party = Party().get_by('id', id)
        if party:
            fields = [name_key]
            data = check_form_data(party_key, request, fields)
            if not data:
                return error(
                    "No data was provided, "
                    "fields [name] required to edit party", 400)
            new_name = data[name_key]
            if Party().get_by('name', new_name):
                return error('Name already exists', 409)
            invalid = invalid_name(new_name, party_key)
            if invalid:
                return error(invalid['message'], invalid['code'])
            new = Party(Id=id).patch('name', new_name, id)
            return success(200, [new])
        return not_found_resp(party_key)
    except Exception as e:
        return system_unavailable(e)
