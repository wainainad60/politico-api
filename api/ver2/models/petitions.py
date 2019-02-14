from .skeleton import Skeleton
from .users import User
from .offices import Office
from api.strings import id_key, status_400, status_404
from api.ver1.offices.strings import office_key
from api.ver1.ballot.strings import createdBy_key, createdOn_key, body_key
from api.ver2.utils.validators import is_number, valid_date, no_date_diff
from api.ver2.utils.strings import evidence_key


class Petition(Skeleton):
    def __init__(self, created_on=None, created_by=None, office_id=None, body=None, evidence=None):
        super().__init__('Vote', 'politico_votes')

        self.created_on = created_on
        self.created_by = created_by
        self.office = office_id
        self.body = body
        self.evidence = evidence
        self.Id = None

    def create(self):
        data = super().add(
            createdOn_key + ',' + createdBy_key + ', ' + office_key + ', ' + body_key+ ', ' + evidence_key,
            self.created_on, self.created_by, self.office, self.body, self.evidence
        )
        self.Id = data.get(id_key)
        return data

    def to_json(self):
        # get the object as a json
        return {
            id_key: self.Id,
            createdOn_key: self.created_on,
            createdBy_key: self.created_by,
            office_key: self.office,
            body_key: self.body,
            evidence_key: self.evidence
        }

    def from_json(self, json):
        self.__init__(
            json[createdOn_key],
            json[createdBy_key],
            json[office_key],
            json[body_key],
            json[evidence_key]
        )
        self.Id = json[id_key]
        return self

    def validate_petition(self):
        if not is_number(self.created_by):
            self.message = "String types are not allowed for Created By field"
            self.code = status_400
            return False

        if not is_number(self.office):
            self.message = "String types are not allowed for Office ID field"
            self.code = status_400
            return False

        if not User().get_by(id_key, self.created_by):
            self.message = 'Selected User does not exist'
            self.code = status_404
            return False

        if not Office().get_by(id_key, self.office):
            self.message = 'Selected Office does not exist'
            self.code = status_404
            return False

        if valid_date(self.created_on):
            self.message = "Invalid date format; expected format is DD/MM/YY e.g 12/12/19"
            self.code = status_400
            return False

        if no_date_diff(self.created_on):
            self.message = "The date entered doesn't match today's date"
            self.code = status_400
            return False

        return super().validate_self()

