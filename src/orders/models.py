from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, select
from src import db, BaseMixin, ReprMixin


class OrderStatus(db.Model, BaseMixin, ReprMixin):
    __repr_fields__ = ['order_id', 'status_id']

    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)

    order = db.relationship('Order', foreign_keys=[order_id])
    status = db.relationship('Status', foreign_keys=[status_id])


class Status(db.Model, BaseMixin, ReprMixin):

    name = db.Column(db.String(20), unique=True, nullable=False)
    code = db.Column(db.SmallInteger, unique=True, nullable=False)


class Order(db.Model, BaseMixin, ReprMixin):

    __repr_fields__ = ['id', 'customer_id']

    edit_stock = db.Column(db.Boolean(), default=True)
    sub_total = db.Column(db.Float(precision=2), default=0, nullable=True)
    total = db.Column(db.Float(precision=2), default=0, nullable=True)

    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=True)
    retail_shop_id = db.Column(db.Integer, db.ForeignKey('retail_shop.id'), nullable=True)
    current_status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=True)

    items = db.relationship('Item', uselist=True, back_populates='order', lazy='dynamic')
    customer = db.relationship('Customer', foreign_keys=[customer_id])
    retail_shop = db.relationship('RetailShop', foreign_keys=[retail_shop_id])
    discounts = db.relationship('Discount', secondary='order_discount')
    current_status = db.relationship('Status', uselist=False, foreign_keys=[current_status_id])
    time_line = db.relationship('Status', secondary='order_status')

    @hybrid_property
    def total_discount(self):
        return sum([discount.value if discount.type == 'VALUE' else float(self.total*discount/100)
                    for discount in self.discounts])

    @hybrid_property
    def total_amount(self):
        return self.total - self.total_discount

    @hybrid_property
    def items_count(self):
        return self.order_items.with_entities(func.Count(Item.id)).scalar()

    @items_count.expression
    def items_count(cls):
        return select([func.Count(Item.id)]).where(Item.order_id == cls.id).as_scalar()


class Item(db.Model, BaseMixin, ReprMixin):

    __repr_fields__ = ['id', 'order_id', 'product_id']

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    unit_price = db.Column(db.Float(precision=2))
    quantity = db.Column(db.SmallInteger)
    discount = db.Column(db.FLOAT(precision=2), default=0, nullable=False)

    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=True)
    combo_id = db.Column(db.Integer, db.ForeignKey('combo.id'), nullable=True)

    product = db.relationship('Product', foreign_keys=[product_id])
    order = db.relationship('Order', foreign_keys=[order_id], single_parent=True, back_populates='items')
    taxes = db.relationship('ItemTax', uselist=True, cascade='all, delete-orphan',
                            back_populates='item')
    add_ons = db.relationship('ItemAddOn', uselist=True, cascade='all, delete-orphan',
                              back_populates='item')
    stock = db.relationship('Stock', foreign_keys=[stock_id], single_parent=True, back_populates='order_items')

    @hybrid_property
    def total_price(self):
        return float(self.unit_price * self.quantity)

    @hybrid_property
    def discount_amount(self):
        return float((self.total_price*self.discount)/100)

    @hybrid_property
    def is_combo(self):
        return self.combo_id is not None


class ItemAddOn(db.Model, BaseMixin, ReprMixin):

    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    add_on_id = db.Column(db.Integer, db.ForeignKey('add_on.id'))

    add_on = db.relationship('AddOn', foreign_keys=[add_on_id])
    item = db.relationship('Item', back_populates='add_ons', foreign_keys=[item_id])


class ItemTax(db.Model, BaseMixin):

    tax_value = db.Column(db.Float(precision=2))

    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    tax_id = db.Column(db.Integer, db.ForeignKey('tax.id'))

    tax = db.relationship('Tax', foreign_keys=[tax_id])
    item = db.relationship('Item', back_populates='taxes', foreign_keys=[item_id])


class OrderDiscount(db.Model, BaseMixin, ReprMixin):
    __repr_fields__ = ['order_id', 'discount_id']

    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    discount_id = db.Column(db.Integer, db.ForeignKey('discount.id'), nullable=False)

    order = db.relationship('Order', foreign_keys=[order_id])
    discount = db.relationship('Discount', foreign_keys=[discount_id])


class Discount(db.Model, BaseMixin, ReprMixin):

    name = db.Column(db.String(55), nullable=True)
    value = db.Column(db.Float(precision=2), nullable=False)
    type = db.Column(db.Enum('PERCENTAGE', 'FIXED', name='varchar'), nullable=False, default='PERCENTAGE')

    orders = db.relationship('Order', secondary='order_discount')

