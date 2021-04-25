from datetime import date
import urllib3
from functools import wraps
from flask import request, abort
import connexion
import jwt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from invoice import *

# dummy reference for migrations only


invoice_schema = InvoiceSchema()
invoices_schema = InvoiceSchema(many=True)
JWT_SECRET = 'INVOICES MS SECRET'
JWT_LIFETIME_SECONDS = 600000

user_ms_url = 'http://localhost:5001/api'
payments_ms_url = 'http://localhost:5002/api'
inventory_ms_url = 'http://localhost:5003/api'
statistics_ms_url = 'http://localhost:5004/api'

http = urllib3.PoolManager()


def has_role(arg):
    def has_role_inner(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            try:
                headers = request.headers
                if 'AUTHORIZATION' in headers:
                    token = headers['AUTHORIZATION'].split(' ')[1]
                    decoded_token = decode_token(token)
                    if 'admin' in decoded_token['roles']:
                        return fn(*args, **kwargs)
                    for role in arg:
                        if role in decoded_token['roles']:
                            return fn(*args, **kwargs)
                    abort(401)
                return fn(*args, **kwargs)
            except Exception as e:
                abort(401)

        return decorated_view

    return has_role_inner


@has_role(['admin', 'shopping_cart'])
def create_invoice(invoice_body):
    # Get User Details from User microservice
    user = http.request('GET', f"{user_ms_url}/details/{invoice_body['user_id']}")

    # Get Transaction details from Payments microservice
    transaction = http.request('GET', f"{payments_ms_url}/transactions/{invoice_body['transaction_id']}")

    # Get Items from Inventory microservice
    items = []
    for item in invoice_body['item_list']:
        if item.type == 'Rent':
            new_item = http.request('GET', f"{inventory_ms_url}/get/product_rent/{item.id}")
            items.append(new_item)
        elif item.type == 'Buy':
            new_item = http.request('GET', f"{inventory_ms_url}/get/product_buy/{item.id}")
            items.append(new_item)

    new_invoice = Invoice(name=user.name, surname=user.surname,
                          username=user.username, country=user.country,
                          city=user.city, postal_code=user.postal_code, address=user.address,
                          price=transaction.amount, date=date.today(), items=items)

    # new_invoice = Invoice(id=1, name='Petko', surname='Petkovski',
    #                       user_id=1, country='Macedonia',
    #                       city='Debar', postal_code=1250, address='Ulica br.11/11',
    #                       price=69.99, date=date.today())
    db.session.add(new_invoice)
    db.session.commit()

    # Notify discount microservice if a coupon is bought : TODO

    # Notify statistics microservice : TODO Do this for each item :
    # http.request('POST', f"{statistics_ms_url}/invoice/", data = {'user_id': invoice_body['user_id'], 'type_of_product': item.type, 'quantity': item.quantity})


@has_role(['admin'])
def get_invoice_by_id(invoice_id):
    found_invoice = db.session.query(Invoice).filter_by(id=invoice_id).first()
    if found_invoice:
        return result_invoice(found_invoice)
    else:
        return {'error': '{} not found'.format(invoice_id)}, 404


@has_role(['admin'])
def get_invoice_by_user(user_id):
    user_invoices = db.session.query(Invoice).filter_by(user_id).all()
    if user_invoices:
        return result_invoice(user_invoices)
    else:
        return {'error': 'No invoices for user {}'.format(user_id)}, 404


@has_role(['admin'])
def get_all():
    all_invoices = db.session.query(Invoice).all()
    if all_invoices:
        return result_invoice(all_invoices)
    else:
        return {'error': 'No invoices found'}, 404


# def person_add(person_body):
#     new_person = Person(name=person_body['name'], surname=person_body['surname'])
#     db.session.add(new_person)
#     db.session.commit()
#
#
# def person_find(person_name):
#     found_person = db.session.query(Person).filter_by(name=person_name).first()
#     if found_person:
#         return {'id': found_person.id, 'name': found_person.name, 'surname': found_person.surname}
#     else:
#         return {'error': '{} not found'.format(person_name)}, 404


def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])


connexion_app = connexion.App(__name__, specification_dir="./")
app = connexion_app.app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
connexion_app.add_api("api.yml")

from models import Invoice

if __name__ == "__main__":
    connexion_app.run(host='0.0.0.0', port=5000, debug=True)
