import connexion
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


def get_test1(test1_id):
    return {'id': 1, 'name': 'name', 'entered_id': test1_id}


def person_add(person_body):
    new_person = Person(name=person_body['name'], surname=person_body['surname'])
    db.session.add(new_person)
    db.session.commit()


def person_find(person_name):
    found_person = db.session.query(Person).filter_by(name=person_name).first()
    if found_person:
        return { 'id': found_person.id, 'name': found_person.name, 'surname': found_person.surname}
    else:
        return {'error': '{} not found'.format(person_name)}, 404


connexion_app = connexion.App(__name__, specification_dir="./")
app = connexion_app.app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
connexion_app.add_api("api.yml")

# dummy reference for migrations only
from models import User, Person
from models2 import Person2

if __name__ == "__main__":
    connexion_app.run(host='0.0.0.0', port=5000, debug=True)
