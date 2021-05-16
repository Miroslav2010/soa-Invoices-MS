from datetime import date
import time
import requests
import urllib3
from functools import wraps
from flask import request, abort
import connexion
import jwt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from consul import Consul, Check

from invoice import *

# dummy reference for migrations only


consul_port = 8500
service_name = "invoices"
service_port = 5000


def register_to_consul():
    consul = Consul(host='consul', port=consul_port)

    agent = consul.agent

    service = agent.service

    check = Check.http(f"http://{service_name}:{service_port}/api/ui", interval="10s", timeout="5s", deregister="1s")

    service.register(service_name, service_id=service_name, port=service_port, check=check)


def get_service(service_id):
    consul = Consul(host="consul", port=consul_port)

    agent = consul.agent

    service_list = agent.services()

    service_info = service_list[service_id]

    return service_info['Address'], service_info['Port']


def get_service_url(ms_name):
    ms_address, ms_port = get_service(ms_name)

    url = "{}:{}".format(ms_address, ms_port)

    if not url.startswith("http"):
        url = "http://{}".format(url)

    return url


register_to_consul()

invoice_schema = InvoiceSchema()
invoices_schema = InvoiceSchema(many=True)

JWT_SECRET = 'USER MS SECRET'
INVOICES_APIKEY = 'INVOICES MS SECRET'
JWT_LIFETIME_SECONDS = 600000 - 120
AUTH_HEADER = {}
TOKEN_CREATION_TIME = time.time() - JWT_LIFETIME_SECONDS - 1

http = urllib3.PoolManager()


def get_jwt_token():
    user_ms_url = get_service_url('user-ms')

    url = "{}/api/user/{}".format(user_ms_url, 'auth-microservice')

    apikey_json = {"apikey": INVOICES_APIKEY}

    user_auth_microservice_response = requests.post(url=url, json=apikey_json)

    return user_auth_microservice_response.json()


def update_jwt_token():
    global TOKEN_CREATION_TIME
    global AUTH_HEADER

    if time.time() - TOKEN_CREATION_TIME > JWT_LIFETIME_SECONDS:
        print("Updating token")
        jwt_token = get_jwt_token()
        auth_value = "Bearer {}".format(jwt_token)
        AUTH_HEADER = {"Authorization": auth_value}
        TOKEN_CREATION_TIME = time.time()


def has_role(arg):
    def has_role_inner(fn):
        @wraps(fn)
        def decode_view(*args, **kwargs):
            try:
                headers = request.headers
                if 'Authorization' in headers:
                    token = headers['Authorization'].split(' ')[1]
                    decoded_token = decode_token(token)
                    if 'admin' in decoded_token:
                        return fn(*args, **kwargs)
                    for role in arg:
                        if role in decoded_token['roles']:
                            return fn(*args, **kwargs)
                    abort(404)
                return fn(*args, **kwargs)
            except Exception as e:
                abort(401)

        return decode_view

    return has_role_inner


@has_role(['invoices', 'shopping_cart'])
def create_invoice(invoice_body):
    global AUTH_HEADER
    user_url = get_service_url('user-ms')
    payments_url = get_service_url('payments')
    inventory_url = get_service_url('inventory')
    statistics_url = get_service_url('statistics')
    discounts_url = get_service_url('discounts')

    update_jwt_token()
    # Get User Details from User microservice
    user = requests.get(url=f"{user_url}/details/{invoice_body['user_id']}", headers=AUTH_HEADER)

    # Get Transaction details from Payments microservice
    transaction = requests.get(url=f"{payments_url}/transactions/{invoice_body['transaction_id']}", headers=AUTH_HEADER)
    # Get Items from Inventory microservice
    items = []
    for item in invoice_body['item_list']:

        requests.post(url=f"{statistics_url}/invoice/", headers=AUTH_HEADER,
                      json={'user_id': invoice_body['user_id'], 'type_of_product': item.type,
                            'quantity': item.quantity})
        it = Item()
        if item.type == 'Rent':
            new_item = requests.get(url=f"{inventory_url}/get/product_rent/{item.id}", headers=AUTH_HEADER)
            it.id = item.id
            it.name = new_item.name
            it.type = item.type
            it.description = new_item.description
            it.duration = item.quantity
            items.append(it)
        elif item.type == 'Buy':
            new_item = requests.get(url=f"{inventory_url}/get/product_rent/{item.id}", headers=AUTH_HEADER)

            it.id = item.id
            it.name = new_item.name
            it.type = item.type
            it.description = new_item.description
            it.quantity = item.quantity
            items.append(it)
        elif item.type == 'Coupon':
            new_item = requests.get(url=f"{inventory_url}/get/product_rent/{item.id}", headers=AUTH_HEADER)
            requests.post(url=f"{discounts_url}/coupon/create", headers=AUTH_HEADER,
                          json={'id': item.id, 'type': new_item.type, 'userId': invoice_body['user_id']})

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


@has_role(['invoices'])
def get_invoice_by_id(invoice_id):
    found_invoice = db.session.query(Invoice).filter_by(id=invoice_id).first()
    if found_invoice:
        return result_invoice(found_invoice)
    else:
        return {'error': '{} not found'.format(invoice_id)}, 404


@has_role(['invoices'])
def get_invoices_by_user(user_id):
    user_invoices = db.session.query(Invoice).filter_by(user_id).all()
    if user_invoices:
        return result_invoice(user_invoices)
    else:
        return {'error': 'No invoices for user {}'.format(user_id)}, 404


@has_role(['invoices'])
def get_all():
    all_invoices = db.session.query(Invoice).all()
    if all_invoices:
        return result_invoice(all_invoices)
    else:
        return {'error': 'No invoices found'}, 404


@has_role(['invoices'])
def delete_invoice(invoice_id):
    invoice_delete = db.session.query(Invoice).filter_by(id=invoice_id).first()
    if invoice_delete:
        db.session.query(Invoice).filter_by(id=invoice_id).delete()
        db.session.commit()
    else:
        return {'error': '{} not found'.format(invoice_id)}, 404


def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])


connexion_app = connexion.App(__name__, specification_dir="./")
app = connexion_app.app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
connexion_app.add_api("api.yml")

from models import Invoice, Item

if __name__ == "__main__":
    connexion_app.run(host='0.0.0.0', port=5000, debug=True)
