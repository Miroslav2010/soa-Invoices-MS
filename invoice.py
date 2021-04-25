from marshmallow import Schema, fields


class InvoiceSchema(Schema):
    id = fields.Number()
    name = fields.String()
    surname = fields.String()
    user_id = fields.Number()
    country = fields.String()
    city = fields.String()
    postal_code = fields.String()
    address = fields.String()
    price = fields.Float()
    currency = fields.String()
    date = fields.Date()


invoice_schema = InvoiceSchema()


def result_invoice(invoice):
    result = dict(id=invoice.id, name=invoice.name, surname=invoice.surname, user_id=invoice.user_id,
                  country=invoice.country,
                  city=invoice.city, postal_code=invoice.postal_code, address=invoice.address, price=invoice.price, date=invoice.date)
    return invoice_schema.dump(result)