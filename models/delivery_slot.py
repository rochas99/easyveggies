from . import db
from sqlalchemy import Sequence


class DeliverySlot(db.Model):
    __bind_key__ = 'db'
    id = db.Column(db.Integer, Sequence('DeliverySlot_sequence'), unique=True, nullable=False, primary_key=True)
    slot_time = db.Column(db.String(100), nullable=False)
    availability = db.Column(db.Boolean, default=True)
