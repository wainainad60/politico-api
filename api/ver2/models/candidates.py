from .skeleton import Skeleton
from .users import User
from .offices import Office
from .parties import Party
from api.strings import id_key, status_400, status_404, status_409
from api.ver1.offices.strings import office_key
from api.ver1.parties.strings import party_key
from api.ver1.ballot.strings import candidate_key
from api.ver2.utils.validators import is_number


class Candidate(Skeleton):
    def __init__(self, Id=None, party_id=None, office_id=None, candid_id=None):
        super().__init__('Candidate', 'politico_candidates')

        self.party = party_id
        self.office = office_id
        self.candidate = candid_id
        self.Id = Id

    def create(self):
        data = super().add(
            party_key + ',' + office_key + ', ' + candidate_key, 
            self.party, self.office, self.candidate
        )
        self.Id = data.get(id_key)
        return data

    def to_json(self):
        # get the object as a json
        return {
            id_key: self.Id,
            party_key: self.party,
            office_key: self.office,
            candidate_key: self.candidate
        }

    def from_json(self, json):
        self.__init__(
            json[party_key], 
            json[office_key], 
            json[candidate_key])
        self.Id = json[id_key]
        return self

    def validate_candidate(self):
        if not is_number(self.party):
            self.message = "String types are not allowed for Party ID field"
            self.code = status_400
            return False
        
        if not is_number(self.candidate):
            self.message = "String types are not allowed for Candidate ID field"
            self.code = status_400
            return False
        
        if not is_number(self.office):
            self.message = "String types are not allowed for Office ID field"
            self.code = status_400
            return False

        if not User().get_by(id_key, self.candidate):
            self.message = 'Selected User does not exist'
            self.code = status_404
            return False

        if self.get_by(candidate_key, self.candidate):
            self.message = "{} is already registered".format(self.entity)
            self.code = status_409
            return False

        if not Office().get_by(id_key, self.office):
            self.message = 'Selected Office does not exist'
            self.code = status_404
            return False

        if not Party().get_by(id_key, self.party):
            self.message = 'Selected Party does not exist'
            self.code = status_404
            return False

        return super().validate_self()


