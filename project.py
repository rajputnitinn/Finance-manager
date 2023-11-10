from flask import *
import datetime
from bson.objectid import ObjectId
from database import MongoDBHelper
import hashlib
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'financemanager-key-1'


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'your_username'
app.config['MAIL_PASSWORD'] = 'your_password'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

scheduler = BackgroundScheduler()
scheduler.start()

selected_expenses = []


@app.route("/")
def login_page():
    return render_template('login.html')


@app.route("/register")
def register():
    return render_template('register.html')


@app.route("/home")
def home():
    if 'user_email' in session:
        return render_template('home.html', email=session['user_email'])
    else:
        return redirect("/")


@app.route("/bills")
def view_bills():
    if 'user_id' not in session:
        return redirect("/")
    return render_template('bills.html')


@app.route("/shopping")
def view_shopping_expenses():
    if 'user_id' not in session:
        return redirect("/")
    return render_template('shopping.html')


@app.route("/study")
def view_study_expenses():
    if 'user_id' not in session:
        return redirect("/")
    return render_template('study.html')


@app.route("/food")
def view_food_grocery_expenses():
    if 'user_id' not in session:
        return redirect("/")
    return render_template('food.html')


@app.route("/register-user", methods=['POST'])
def register_user():
    user_data = {
        'name': request.form['name'],
        'email': request.form['email'],
        'password': hashlib.sha256(request.form['pswd'].encode('utf-8')).hexdigest(),
        'members': request.form['members'],
        'kids': request.form['kids'],
        'income': request.form['income'],
        'housing_status': request.form['housing_status'],
        'createdOn': datetime.datetime.today()
    }
    db = MongoDBHelper(collection="user")
    result = db.insert(user_data)

    user_id = result.inserted_id
    session['user_id'] = str(user_id)
    session['user_name'] = user_data['name']
    session['user_email'] = user_data['email']

    return redirect("/home")


@app.route("/login-user", methods=['POST'])
def user_login():
    user_data = {
        'email': request.form['email'],
        'password': hashlib.sha256(request.form['pswd'].encode('utf-8')).hexdigest(),
    }
    db = MongoDBHelper(collection="user")
    documents = db.fetch(user_data)

    if len(documents) == 1:
        session['user_id'] = str(documents[0]['_id'])
        session['user_email'] = documents[0]['email']
        session['user_name'] = documents[0]['name']
        return redirect("/profile")
    else:
        return render_template('error.html')


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('user_name', None)
    return redirect("/")


@app.route('/add-expenses', methods=['POST'])
def add_expenses():
    global selected_expenses
    expense = request.form.get('expense')
    if expense:
        selected_expenses.append(expense)
    return render_template('index.html', selected_expenses=selected_expenses)


@app.route('/bills', methods=['POST'])
def save_bills():
    if 'user_id' not in session:
        return redirect("/")

    due_date_str = request.form['dueDate']
    due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d')

    reminder_date = due_date - datetime.timedelta(days=2)

    bill_data = {
        'user_id': ObjectId(session['user_id']),
        'bill_type': request.form['billType'],
        'bill_amount': float(request.form['billAmount']),
        'current_date': datetime.datetime.now(),
        'due_date': due_date,
        'reminder_date': reminder_date,
        'bill_description': request.form['billDescription'],
        'createdOn': datetime.datetime.today()
    }

    db = MongoDBHelper(collection="bills")
    result = db.insert(bill_data)


    schedule_email_reminder(bill_data, session['user_email'])

    return render_template('success.html', message="Bill added successfully.")


def schedule_email_reminder(bill_data, user_email):

    reminder_date = bill_data['reminder_date']


    scheduler.add_job(
        send_reminder_email,
        'date',
        run_date=reminder_date,
        args=[bill_data, user_email]
    )


def send_reminder_email(bill_data, user_email):
    try:
        msg = Message('Bill Reminder', sender='your_email@gmail.com', recipients=[user_email])
        msg.body = f"Reminder: Your {bill_data['bill_type']} bill is due on {bill_data['due_date']}. Don't forget to pay it."
        mail.send(msg)
        print(f"Reminder email sent to {user_email}")
    except Exception as e:
        print(f"Failed to send reminder email to {user_email}: {str(e)}")


@app.route('/shopping', methods=['POST'])
def save_shopping_expense():
    if 'user_id' not in session:
        return redirect("/")

    shopping_data = {
         'user_id': ObjectId(session['user_id']),
        'clothing': request.form['clothing'],
        'personal_care': request.form['personal_care'],
        'entertainment': request.form['entertainment'],
        'createdOn': datetime.datetime.today()
    }

    db = MongoDBHelper(collection="shopping_expenses")
    result = db.insert(shopping_data)

    return render_template('success.html', message="Shopping Expenses added successfully.")

@app.route('/study', methods=['GET', 'POST'])
def study():
    if request.method == 'POST':
        user_id: ObjectId(session['user_id'])
        name_of_kid = request.form['name_of_kid']
        fees_type = request.form['feesType']
        fees_amount = request.form['feesAmount']
        tuition = request.form['tuition']
        books = request.form['books']
        fees = request.form['fees']
        loans = request.form['loans']

        study_data = {
            'user_id': ObjectId(session['user_id']),
            'name_of_kid': name_of_kid,
            'feesType': fees_type,
            'feesAmount': fees_amount,
            'tuition': tuition,
            'books': books,
            'fees': fees,
            'loans': loans,
            'createdOn': datetime.datetime.now()
        }

    db = MongoDBHelper(collection="study_expenses")
    result = db.insert(study_data)

    return render_template('success.html', message="Study Expenses added successfully.")

@app.route("/food", methods=['POST'])
def save_food_expense():
    if request.method == 'POST':
        user_id: ObjectId(session['user_id'])
        groceries: request.form['groceries']
        eating_out: request.form['eating-out']


    food_data = {
         'user_id': ObjectId(session['user_id']),
         'groceries': request.form['groceries'],
         'eating_out': request.form['eating-out'],
         'createdOn': datetime.datetime.today()
    }

    db = MongoDBHelper(collection="food_grocery")
    result = db.insert(food_data)

    return render_template('success.html', message="Study Expenses added successfully.")




@app.route("/profile")
def user_profile():
    if 'user_id' not in session:
        return redirect("/")

    db = MongoDBHelper(collection="user")
    user_data = db.fetch({"_id": ObjectId(session['user_id'])})

    if not user_data:
        return render_template('error.html', message="User not found")

    user_data = user_data[0]

    return render_template('profile.html', user=user_data)


@app.route("/fetch-bills")
def fetch_bills():
    if 'user_id' not in session:
        return redirect("/")
    db = MongoDBHelper(collection="bills")
    bills = db.fetch({"user_id": ObjectId(session['user_id'])})
    return render_template('billss.html', bills=bills)


@app.route("/fetch-shopping")
def fetch_shopping():
    if 'user_id' not in session:
        return redirect("/")

    db = MongoDBHelper(collection="shopping_expenses")
    shopping_expenses = db.fetch({"user_id": ObjectId(session['user_id'])})

    return render_template('shoppingg.html', shopping_expenses=shopping_expenses)


@app.route("/fetch-study")
def fetch_study():
    if 'user_id' not in session:
        return redirect("/")
    db = MongoDBHelper(collection="study_expenses")
    study_expenses = db.fetch({"user_id": ObjectId(session['user_id'])})
    return render_template('studyy.html', study_expenses=study_expenses)

@app.route("/fetch-food")
def fetch_food():
    if 'user_id' not in session:
        return redirect("/")
    db = MongoDBHelper(collection="food_grocery")
    food_grocery_expenses = db.fetch({"user_id": ObjectId(session['user_id'])})
    return render_template('foodd.html', food_grocery_expenses=food_grocery_expenses)
@app.route("/delete-bill/<string:bill_id>")
def delete_bill(bill_id):
    if 'user_id' not in session:
        return redirect("/")

    db = MongoDBHelper(collection="bills")
    result = db.delete({"_id": ObjectId(bill_id)})

    return render_template('success.html', message="Bills deleted successfully")

@app.route("/delete-study/<string:study_id>")
def delete_study(study_id):
    if 'user_id' not in session:
        return redirect("/")

    db = MongoDBHelper(collection="study_expenses")
    result = db.delete({"_id": ObjectId(study_id)})

    return render_template('success.html', message="Study Expenses deleted successfully")


@app.route("/delete-shopping/<string:shopping_id>")
def delete_shopping(shopping_id):
    if 'user_id' not in session:
        return redirect("/")

    db = MongoDBHelper(collection="shopping_expenses")
    result = db.delete({"_id": ObjectId(shopping_id)})

    return render_template('success.html', message="Shopping Expenses deleted successfully")


@app.route("/delete-food/<string:food_id>")
def delete_food(food_id):
    if 'user_id' not in session:
        return redirect("/")

    db = MongoDBHelper(collection="food_grocery")
    result = db.delete({"_id": ObjectId(food_id)})

    return render_template('success.html', message=" Expenses deleted successfully")



if __name__ == "__main__":
    app.run(debug=True)
