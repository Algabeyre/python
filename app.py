import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask aqlchemy import text
# KEEP YOUR WERKZEUG IMPORTS HERE SO THEY DON'T GO AWAY:
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret')

# --- This is the new database configuration code ---
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///budget.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# --------------------------------------------------

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    user = db.relationship('User', backref=db.backref('transactions', lazy=True))


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view


@app.route('/')
@login_required
def index():
    user_id = session['user_id']
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    income = sum(t.amount for t in transactions if t.type == 'income')
    expenses = sum(t.amount for t in transactions if t.type == 'expense')
    balance = income - expenses

    from collections import defaultdict
    category_totals = defaultdict(float)
    for t in transactions:
        if t.type == 'expense':
            category_totals[t.category] += t.amount

    categories = list(category_totals.keys())
    amounts = list(category_totals.values())
    palette = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#C9CBCF', '#8BC34A', '#E91E63', '#00BCD4',
        '#9C27B0', '#FFEB3B', '#795548', '#607D8B', '#F44336'
    ]
    colors = [palette[i % len(palette)] for i in range(len(categories))]

    return render_template(
        'index.html',
        transactions=transactions,
        income=income,
        expenses=expenses,
        balance=balance,
        categories=categories,
        amounts=amounts,
        colors=colors,
        username=session.get('username')
    )


@app.route('/add', methods=['POST'])
@login_required
def add():
    t_type = request.form['type']
    category = request.form['category']
    amount = float(request.form['amount'])
    description = request.form['description']
    transaction = Transaction(
        type=t_type,
        category=category,
        amount=amount,
        description=description,
        user_id=session['user_id']
    )
    db.session.add(transaction)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    transaction = Transaction.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    transaction = Transaction.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    if request.method == 'POST':
        transaction.type = request.form['type']
        transaction.category = request.form['category']
        transaction.amount = float(request.form['amount'])
        transaction.description = request.form['description']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', transaction=transaction)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm = request.form['confirm_password']

        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Choose another one.', 'error')
            return redirect(url_for('register'))

        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user is None or not check_password_hash(user.password_hash, password):
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

        session.clear()
        session['user_id'] = user.id
        session['username'] = user.username
        session.permanent = True

        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- MOVE THIS OUTSIDE SO GUNICORN RUNS IT ---
with app.app_context():
    db.create_all()  # This safely creates tables only if they don't exist

# ---------------------------------------------

if __name__ == '__main__':
    # Keep app.run here; it will only fire when you test locally
    app.run(debug=True)
 

