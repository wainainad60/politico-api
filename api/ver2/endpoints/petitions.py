from flask import request, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.ver2.utils.strings import evidence_key, petition_key
from api.strings import post_method, status_201, get_method
from api.ver1.ballot.strings import body_key
from api.ver1.utils import check_form_data, no_entry_resp, \
    field_missing_resp, error, success
from api.ver1.offices.strings import office_key
from api.ver2.models.petitions import Petition
from api.ver2.utils.utilities import system_unavailable


petitions_bp = Blueprint('petitions_bp', __name__)


@petitions_bp.route('/petitions/', methods=[post_method, get_method])
@jwt_required
def petitions():
    try:
        if request.method == post_method:
            fields = [office_key, body_key, evidence_key]
            data = check_form_data(petition_key, request, fields)
            if data:
                try:
                    user = get_jwt_identity()
                    petition = Petition(
                        created_by=user,
                        office_id=data[office_key],
                        body=data[body_key],
                        evidence=data[evidence_key]
                    )
                    if petition.validate_petition():
                        petition.create()
                        return success(status_201, [petition.to_json()])
                    else:
                        return error(petition.message, petition.code)
                except Exception as e:
                    return field_missing_resp(petition_key, fields, e.args[0])
            else:
                return no_entry_resp(petition_key, fields)
        elif request.method == get_method:
            return success(200, Petition().fetch_petitions())
    except Exception as e:
        return system_unavailable(e)
