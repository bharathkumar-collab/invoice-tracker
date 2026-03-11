from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import json, os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///invoiceflow.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── Models ───────────────────────────────────────────────────

class User(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    biz_name   = db.Column(db.String(150), default='My Business')
    biz_email  = db.Column(db.String(150), default='')
    biz_phone  = db.Column(db.String(50), default='')
    biz_web    = db.Column(db.String(150), default='')
    biz_addr   = db.Column(db.Text, default='')
    currency   = db.Column(db.String(5), default='$')
    prefix     = db.Column(db.String(20), default='INV-')
    next_num   = db.Column(db.Integer, default=1001)
    due_days   = db.Column(db.Integer, default=30)
    tax_rate   = db.Column(db.Float, default=0)
    tax_label  = db.Column(db.String(20), default='Tax')
    tax_num    = db.Column(db.String(50), default='')
    def_notes  = db.Column(db.Text, default='Thank you for your business!')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    clients    = db.relationship('Client', backref='user', lazy=True, cascade='all, delete')
    invoices   = db.relationship('Invoice', backref='user', lazy=True, cascade='all, delete')

    def to_settings(self):
        return {
            'bizName': self.biz_name, 'bizEmail': self.biz_email,
            'bizPhone': self.biz_phone, 'bizWeb': self.biz_web,
            'bizAddr': self.biz_addr, 'currency': self.currency,
            'prefix': self.prefix, 'nextNum': self.next_num,
            'dueDays': self.due_days, 'taxRate': self.tax_rate,
            'taxLabel': self.tax_label, 'taxNum': self.tax_num,
            'defaultNotes': self.def_notes
        }

class Client(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name       = db.Column(db.String(150), nullable=False)
    email      = db.Column(db.String(150), default='')
    phone      = db.Column(db.String(50), default='')
    web        = db.Column(db.String(150), default='')
    addr       = db.Column(db.Text, default='')
    notes      = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    invoices   = db.relationship('Invoice', backref='client', lazy=True)

    def to_dict(self):
        inv_total = sum(i.total for i in self.invoices)
        return {
            'id': self.id, 'name': self.name, 'email': self.email,
            'phone': self.phone, 'web': self.web, 'addr': self.addr,
            'notes': self.notes, 'invoiceCount': len(self.invoices),
            'revenue': inv_total
        }

class Invoice(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id   = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    number      = db.Column(db.String(50), nullable=False)
    date        = db.Column(db.String(20), nullable=False)
    due_date    = db.Column(db.String(20), default='')
    bill_to     = db.Column(db.Text, default='')
    notes       = db.Column(db.Text, default='')
    status      = db.Column(db.String(20), default='pending')
    items_json  = db.Column(db.Text, default='[]')
    subtotal    = db.Column(db.Float, default=0)
    tax         = db.Column(db.Float, default=0)
    total       = db.Column(db.Float, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'clientId': self.client_id,
            'clientName': self.client.name if self.client else '',
            'number': self.number, 'date': self.date, 'dueDate': self.due_date,
            'billTo': self.bill_to, 'notes': self.notes, 'status': self.status,
            'items': json.loads(self.items_json or '[]'),
            'sub': self.subtotal, 'tax': self.tax, 'total': self.total,
            'createdAt': self.created_at.isoformat()
        }

# ─── Auth helpers ─────────────────────────────────────────────

def current_user():
    uid = session.get('user_id')
    return User.query.get(uid) if uid else None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user():
            return jsonify({'error': 'Unauthorized'}), 401
    return decorated

# ─── Pages ────────────────────────────────────────────────────

@app.route('/')
def index():
    if current_user():
        return render_template('app.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ─── Auth API ─────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    d = request.json
    if User.query.filter_by(email=d['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    u = User(email=d['email'], password=generate_password_hash(d['password']),
             biz_name=d.get('bizName', 'My Business'))
    db.session.add(u)
    db.session.commit()
    session['user_id'] = u.id
    return jsonify({'ok': True, 'settings': u.to_settings()})

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    u = User.query.filter_by(email=d['email']).first()
    if not u or not check_password_hash(u.password, d['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    session['user_id'] = u.id
    return jsonify({'ok': True, 'settings': u.to_settings()})

# ─── Settings API ─────────────────────────────────────────────

@app.route('/api/settings', methods=['GET'])
def get_settings():
    u = current_user()
    if not u: return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(u.to_settings())

@app.route('/api/settings', methods=['POST'])
def save_settings():
    u = current_user()
    if not u: return jsonify({'error': 'Unauthorized'}), 401
    d = request.json
    u.biz_name = d.get('bizName', u.biz_name)
    u.biz_email = d.get('bizEmail', u.biz_email)
    u.biz_phone = d.get('bizPhone', u.biz_phone)
    u.biz_web   = d.get('bizWeb', u.biz_web)
    u.biz_addr  = d.get('bizAddr', u.biz_addr)
    u.currency  = d.get('currency', u.currency)
    u.prefix    = d.get('prefix', u.prefix)
    u.next_num  = int(d.get('nextNum', u.next_num))
    u.due_days  = int(d.get('dueDays', u.due_days))
    u.tax_rate  = float(d.get('taxRate', u.tax_rate))
    u.tax_label = d.get('taxLabel', u.tax_label)
    u.tax_num   = d.get('taxNum', u.tax_num)
    u.def_notes = d.get('defaultNotes', u.def_notes)
    db.session.commit()
    return jsonify({'ok': True})

# ─── Clients API ──────────────────────────────────────────────

@app.route('/api/clients', methods=['GET'])
def get_clients():
    u = current_user()
    if not u: return jsonify({'error': 'Unauthorized'}), 401
    return jsonify([c.to_dict() for c in u.clients])

@app.route('/api/clients', methods=['POST'])
def create_client():
    u = current_user()
    if not u: return jsonify({'error': 'Unauthorized'}), 401
    d = request.json
    c = Client(user_id=u.id, name=d['name'], email=d.get('email',''),
               phone=d.get('phone',''), web=d.get('web',''),
               addr=d.get('addr',''), notes=d.get('notes',''))
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict())

@app.route('/api/clients/<int:cid>', methods=['PUT'])
def update_client(cid):
    u = current_user()
    if not u: return jsonify({'error': 'Unauthorized'}), 401
    c = Client.query.filter_by(id=cid, user_id=u.id).first_or_404()
    d = request.json
    c.name = d.get('name', c.name); c.email = d.get('email', c.email)
    c.phone = d.get('phone', c.phone); c.web = d.get('web', c.web)
    c.addr = d.get('addr', c.addr); c.notes = d.get('notes', c.notes)
    db.session.commit()
    return jsonify(c.to_dict())

@app.route('/api/clients/<int:cid>', methods=['DELETE'])
def delete_client(cid):
    u = current_user()
    if not u: return jsonify({'error': 'Unauthorized'}), 401
    c = Client.query.filter_by(id=cid, user_id=u.id).first_or_404()
    db.session.delete(c)
    db.session.commit()
    return jsonify({'ok': True})

# ─── Invoices API ─────────────────────────────────────────────

@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    u = current_user()
    if not u: return jsonify({'error': 'Unauthorized'}), 401
    invs = Invoice.query.filter_by(user_id=u.id).order_by(Invoice.created_at.desc()).all()
    return jsonify([i.to_dict() for i in invs])

@app.route('/api/invoices', methods=['POST'])
def create_invoice():
    u = current_user()
    if not u: return jsonify({'error': 'Unauthorized'}), 401
    d = request.json
    items = d.get('items', [])
    sub = sum(it['qty'] * it['price'] for it in items)
    tax = sub * u.tax_rate / 100
    inv = Invoice(
        user_id=u.id, client_id=d.get('clientId') or None,
        number=d['number'], date=d['date'], due_date=d.get('dueDate',''),
        bill_to=d.get('billTo',''), notes=d.get('notes',''),
        status=d.get('status','pending'), items_json=json.dumps(items),
        subtotal=sub, tax=tax, total=sub+tax
    )
    db.session.add(inv)
    if d.get('status') != 'draft':
        u.next_num += 1
    db.session.commit()
    return jsonify(inv.to_dict())

@app.route('/api/invoices/<int:iid>', methods=['PUT'])
def update_invoice(iid):
    u = current_user()
    if not u: return jsonify({'error': 'Unauthorized'}), 401
    inv = Invoice.query.filter_by(id=iid, user_id=u.id).first_or_404()
    d = request.json
    items = d.get('items', json.loads(inv.items_json))
    sub = sum(it['qty'] * it['price'] for it in items)
    tax = sub * u.tax_rate / 100
    inv.client_id = d.get('clientId') or None
    inv.number = d.get('number', inv.number)
    inv.date = d.get('date', inv.date)
    inv.due_date = d.get('dueDate', inv.due_date)
    inv.bill_to = d.get('billTo', inv.bill_to)
    inv.notes = d.get('notes', inv.notes)
    inv.status = d.get('status', inv.status)
    inv.items_json = json.dumps(items)
    inv.subtotal = sub; inv.tax = tax; inv.total = sub + tax
    db.session.commit()
    return jsonify(inv.to_dict())

@app.route('/api/invoices/<int:iid>', methods=['DELETE'])
def delete_invoice(iid):
    u = current_user()
    if not u: return jsonify({'error': 'Unauthorized'}), 401
    inv = Invoice.query.filter_by(id=iid, user_id=u.id).first_or_404()
    db.session.delete(inv)
    db.session.commit()
    return jsonify({'ok': True})

# ─── Run ──────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
