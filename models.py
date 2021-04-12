from app import db
import uuid


class Invoice(db.Model):
    generatedId = uuid.uuid1()
    id = db.Column(db.BigInteger, default=generatedId.int, primary_key=True)
    name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False)
    country = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    postal_code = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)


class Item(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.Integer, nullable=True)
