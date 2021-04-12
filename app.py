import connexion
import datetime
# dummy reference for migrations only


from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


def get_test1(test1_id):
    return {'id': 1, 'name': 'name', 'entered_id': test1_id}


def create_invoice(invoice_body):
    # Get User Details from User microservice : TODO

    # Get Transaction details from Payments microservice : TODO

    # Get Items from Inventory microservice : TODO

    new_invoice = Invoice(id=1, name='Petko', surname='Petkovski',
                          username='Petko123', country='Macedonia',
                          city='Debar', postal_code=1250, address='Ulica br.11/11',
                          price=69.99, currency='MKD', date=datetime.date(2021, 4, 8))
    db.session.add(new_invoice)
    db.session.commit()

    # Notify discount microservice if a coupon is bought : TODO

    # Notify statistics microservice : TODO


def get_invoice_by_id(invoice_id):
    found_invoice = db.session.query(Invoice).filter_by(id=invoice_id).first()
    if found_invoice:
        return {'id': found_invoice.id, 'name': found_invoice.name, 'surname': found_invoice.surname,
                'username': found_invoice.username, 'country': found_invoice.country, 'city': found_invoice.city,
                'postal_code': found_invoice.postal_code, 'address': found_invoice.address,
                'price': found_invoice.price, 'currency': found_invoice.currency, 'date': found_invoice.date}
    else:
        return {'error': '{} not found'.format(invoice_id)}, 404


def get_invoices_by_user(user_id):
    user_invoices = db.session.query(Invoice).filter_by(user_id)
    if user_invoices:
        return user_invoices
    else:
        return {'error': 'No invoices for user {}'.format(user_id)}, 404


def get_all():
    all_invoices = db.session.query(Invoice).all()
    if all_invoices:
        return all_invoices
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


connexion_app = connexion.App(__name__, specification_dir="./")
app = connexion_app.app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
connexion_app.add_api("api.yml")

from models import Invoice

if __name__ == "__main__":
    connexion_app.run(host='0.0.0.0', port=5000, debug=True)
