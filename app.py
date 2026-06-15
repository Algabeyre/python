from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))

@app.route('/')
def index():
    transactions = Transaction.query.all()
    income = sum(t.amount for t in transactions if t.type == 'income')
    expenses = sum(t.amount for t in transactions if t.type == 'expense')
    balance = income - expenses

    # Pie chart data for expenses by category
    from collections import defaultdict
    category_totals = defaultdict(float)
    for t in transactions:
        if t.type == 'expense':
            category_totals[t.category] += t.amount
    categories = list(category_totals.keys())
    amounts = list(category_totals.values())
    # Assign a color for each category (cycle through a palette)
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
        colors=colors
    )

@app.route('/add', methods=['POST'])
def add():
    t_type = request.form['type']
    category = request.form['category']
    amount = float(request.form['amount'])
    description = request.form['description']
    transaction = Transaction(type=t_type, category=category, amount=amount, description=description)
    db.session.add(transaction)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    transaction = Transaction.query.get_or_404(id)
    if request.method == 'POST':
        transaction.type = request.form['type']
        transaction.category = request.form['category']
        transaction.amount = float(request.form['amount'])
        transaction.description = request.form['description']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', transaction=transaction)

if __name__ == '__main__':
    if not os.path.exists('budget.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
