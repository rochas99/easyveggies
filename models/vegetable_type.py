from . import db
from sqlalchemy import Sequence

class VegetableType(db.Model):
    __bind_key__ = 'db'
    id = db.Column(db.Integer, Sequence('VegetableType_sequence'), unique=True, nullable=False, primary_key=True)
    type_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))