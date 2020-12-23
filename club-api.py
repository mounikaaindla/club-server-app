from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
import json
import logging
import logging.handlers
import os
import uuid
from flask_cors import CORS

# logger = logging.getLogger(__name__)
# fileConfig('logging.cfg', disable_existing_loggers=False)
# logging.basicConfig(filename='club-api.log',
#                    encoding='utf-8', level=logging.DEBUG)

DATA_FILE_NAME = 'data.json'
LOG_FILE_NAME = 'club-api.log'
DATA = None


def getLogger(logname, logdir, logsize=500*1024, logbackup_count=4):
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    logfile = '%s/%s.log' % (logdir, logname)
    loglevel = logging.DEBUG
    logger = logging.getLogger(logname)
    logger.setLevel(loglevel)
    if logger.handlers is not None and len(logger.handlers) >= 0:
        for handler in logger.handlers:
            logger.removeHandler(handler)
        logger.handlers = []
    loghandler = logging.handlers.RotatingFileHandler(
        logfile, maxBytes=logsize, backupCount=logbackup_count)
    formatter = logging.Formatter(
        '%(asctime)s-%(name)s-%(levelname)s-%(message)s')
    loghandler.setFormatter(formatter)
    logger.addHandler(loghandler)
    return logger


logger = getLogger('club-api', "./logs")

app = Flask(__name__)
CORS(app)
api = Api(app)


def initialize():
    try:
        logger.debug("Intializing JSON object")
        global DATA
        if DATA is None:
            DATA = read_json()
    except:
        logger.error("Error in initializing the data")


def write_json(data):
    with open(DATA_FILE_NAME, "w") as outFile:
        json.dump(data, outFile)
    return True


def read_json():
    # Opening JSON file
    with open(DATA_FILE_NAME, 'r') as openfile:
        # Reading from json file
        logger.debug("Reading the data file")
        json_object = json.load(openfile)
    return json_object


class ClubList(Resource):
    def get_club(self, club_id):
        for club in DATA["clubs"]:
            if club["club_id"] == club_id:
                return club
        return None

    def get(self):
        result = {"list": DATA}
        return result, 200

    def post(self):
        req_club = request.get_json()
        logger.debug(req_club)
        new_club = {}
        club_to_update = None

        if "club_id" in req_club:
            club_id = req_club["club_id"]
            club_to_update = self.get_club(club_id)

        if club_to_update is None:
            club_id = str(uuid.uuid4())
            new_club["club_id"] = club_id
            new_club["club_members"] = []
            new_club["club_name"] = req_club["club_name"]
            new_club["club_address"] = req_club["club_address"]
            DATA["clubs"].append(new_club)
            write_json(DATA)
            return new_club, 201
        else:
            # check for members and data
            club_to_update["club_name"] = req_club["club_name"]
            club_to_update["club_address"] = req_club["club_address"]
            write_json(DATA)
            return club_to_update, 200


class Club(Resource):
    def get_club(self, club_id):
        for club in DATA["clubs"]:
            if club["club_id"] == club_id:
                return club
        return None

    def get(self, club_id):
        club = self.get_club(club_id)
        if not club:
            return abort(404, message="Club {} doesn't exist".format(club_id))
        return club, 200

    def post(self, club_id):
        req_club = request.get_json()
        club = self.get_club(club_id)
        if not club:
            return abort(404, message="Club {} doesn't exist".format(club_id))
        else:
            # check for members and data
            club["club_name"] = req_club["club_name"]
            club["club_address"] = req_club["club_address"]
        write_json(DATA)
        return club, 200

    def delete(self, club_id):
        for club in DATA["clubs"]:
            if club_id == club["club_id"]:
                DATA["clubs"].remove(club)
                write_json(DATA)
                return "Club {} was deleted".format(club_id), 200

        return abort(404, message="Club {} doesn't exist".format(club_id))


class MemberList(Resource):
    def get_club(self, club_id):
        for club in DATA["clubs"]:
            if club["club_id"] == club_id:
                return club
        return None

    def get_member(self, members, member_id):
        for member in members:
            if member["member_id"] == member_id:
                return member
        return None

    def get(self, club_id):
        club = self.get_club(club_id)
        if not club:
            return abort(404, message="Club {} doesn't exist".format(club_id))
        else:
            return club["club_members"], 200

    def post(self, club_id):
        club = self.get_club(club_id)
        if not club:
            return abort(404, message="Club {} doesn't exist".format(club_id))
        req_member = request.get_json()
        logger.debug(req_member)
        new_member = {}
        member_to_update = None

        if "member_id" in req_member:
            member_id = req_member["member_id"]
            member_to_update = self.get_member(club["club_members"], member_id)

        if member_to_update is None:
            member_id = str(uuid.uuid4())
            new_member["member_id"] = member_id
            new_member["member_name"] = req_member["member_name"]
            new_member["member_age"] = req_member["member_age"]
            club["club_members"].append(new_member)
        else:
            # check for members and data
            member_to_update["member_name"] = req_member["member_name"]
            member_to_update["member_age"] = req_member["member_age"]
            new_member = member_to_update
        write_json(DATA)
        return new_member, 201


class Member(Resource):
    def get_club(self, club_id):
        for club in DATA["clubs"]:
            if club["club_id"] == club_id:
                return club
        return None

    def get_member(self, members, member_id):
        for member in members:
            if member["member_id"] == member_id:
                return member
        return None

    def get(self, club_id, member_id):
        club = self.get_club(club_id)
        if not club:
            return abort(404, message="Club {} doesn't exist".format(club_id))

        member = self.get_member(club["club_members"], member_id)
        if member:
            return member, 200

        return "Mmeber {} doesn't exist".format(member_id), 404

    def post(self, club_id, member_id):
        club = self.get_club(club_id)
        req_member = request.get_json()
        if not club:
            return abort(404, message="Club {} doesn't exist".format(club_id))

        new_member = {}
        member_to_update = None

        if "member_id" not in req_member:
            # look into
            member_id = str(uuid.uuid4())
        else:
            member_id = req_member["member_id"]
            member_to_update = self.get_member(club["club_members"], member_id)

        if member_to_update is None:
            new_member["member_id"] = member_id
            new_member["member_name"] = req_member["member_name"]
            new_member["member_age"] = req_member["member_age"]
            club["club_members"].append(new_member)
        else:
            # check for members and data
            member_to_update["member_name"] = req_member["member_name"]
            member_to_update["member_age"] = req_member["member_age"]
            new_member = member_to_update
        write_json(DATA)
        return new_member, 201

    def delete(self, club_id, member_id):
        club = self.get_club(club_id)
        if not club:
            return abort(404, message="Club {} doesn't exist".format(club_id))

        for member in club["club_members"]:
            if member_id == member["member_id"]:
                club["club_members"].remove(member)
                write_json(DATA)
                return "Member {} was deleted".format(member_id), 200

        return abort(404, message="Member {} doesn't exist".format(member_id))


#
# APi resource definition
#
api.add_resource(ClubList, '/clubs')
api.add_resource(Club, '/clubs/<string:club_id>')
api.add_resource(MemberList, '/clubs/<string:club_id>/members')
api.add_resource(Member, '/clubs/<string:club_id>/members/<string:member_id>')

if __name__ == '__main__':
    logger.info("Start ClubApi: listen")
    initialize()
    app.run(debug=True)
