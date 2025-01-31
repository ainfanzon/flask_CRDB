import os.path
import pandas as pd
import psycopg2

from flask import Flask, g, Blueprint, render_template, redirect, url_for, request, abort, session, current_app
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length
#from flask_sqlalchemy import SQLAlchemy
#from sqlalchemy.sql import text
#from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# with Flask-WTF, each web form is represented by a class
# "NameForm" can change; "(FlaskForm)" cannot
# see the route for "/" and "index.html" to see how this is used

# func get_config_variable
def get_config_variable(key):
    with current_app.app_context():
        return current_app.config[key]

# form home
class NameForm(FlaskForm):
    name = StringField('User ID:', validators=[DataRequired(), Length(5, 40)])
    password = PasswordField('Password:', validators=[DataRequired(), Length(5, 40)])
    submit = SubmitField('Sign In')

# form ActionForm
class ActionForm(FlaskForm):
    choices = [('C', 'Create'), ('R', 'Retreive'), ('U', 'Update'), ('D', 'Delete')]
    action = SelectField('Select an option:', choices=choices)
    submit = SubmitField('Submit')

# form Select
class SelectForm(FlaskForm):
    customer_id = StringField('Customer ID:', validators=[DataRequired(), Length(3, 5)])
    submit = SubmitField('Submit')

# form CRUD
class CRUD_Form(FlaskForm):
    customer_id = StringField('Customer ID:', validators=[DataRequired(), Length(3, 5)])
    company_name = StringField('Company Name:', validators=[DataRequired(), Length(3, 40)])
    contact_name = StringField('Contact Name:', validators=[DataRequired(), Length(3, 30)])
    contact_title = StringField('Contact Title:', validators=[DataRequired(), Length(3, 30)])
    address = StringField('Address:', validators=[DataRequired(), Length(3, 60)])
    city = StringField('City:', validators=[DataRequired(), Length(3, 15)])
    region = StringField('Region:', validators=[DataRequired(), Length(3, 15)])
    postal_code = StringField('Postal Code:', validators=[DataRequired(), Length(3, 10)])
    country = StringField('Country:', validators=[DataRequired(), Length(3, 15)])
    phone_number = StringField('Phone Number:', validators=[DataRequired(), Length(7, 24)])
    fax_number = StringField('Fax Number:', validators=[DataRequired(), Length(7, 24)])
    create = SubmitField('Create')
    update = SubmitField('Update')
    retreive = SubmitField('Select')
    delete = SubmitField('Delete')

# blueprint
bp = Blueprint("pages", __name__)

# func connect to the database
def get_db_connection(db):
    conn = psycopg2.connect(
          host = get_config_variable('HOST_IP')
        , database=db
        , user='root'
        , port = get_config_variable('PORT_NUM')
        , sslmode = 'disable'
    )
    return conn

# func home
@bp.route("/", methods=['GET', 'POST'])
def home():
    iam_conn = get_db_connection('iam')
    iam_cur = iam_conn.cursor()
    form = NameForm()
    uid = form.name.data
    pwd = form.password.data
    # Define your query with placeholders
    query = "SELECT user_name, user_passwd, role_name FROM iam_users INNER JOIN iam_roles USING (role_id) WHERE user_name = %s"
    if form.validate_on_submit():
        iam_cur.execute(query, (uid,))
        result_set = iam_cur.fetchone()
        if result_set == None:
            print ("AICA: Nobody there")
        elif result_set[1] == pwd:
            session['username'] = result_set[0]  #Set the user's role in the session
            session['role'] = result_set[2]  #Set the user's role in the session
            g.user = result_set[0]
            match result_set[2]:
                case 'Admin/Super Admin' | 'Auditor' | 'Helpdesk Support' | 'Developer':
                    return redirect(url_for('pages.admin_dashboard'))
                case 'Group Manager' | 'User Manager':
                    return redirect(url_for('pages.mgr_dashboard'))
                case 'External User':
                    return redirect(url_for('pages.usr_dashboard'))
        else:
            print ("Incorrect Password")
        
    return render_template("pages/home.html", form=form)

@bp.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    auth = ('Admin/Super Admin','Auditor')
    if session['role'] not in auth:
#User Manager Group Manager Auditor Helpdesk Support Developer External User
        return render_template("pages/no_access.html")

    return render_template("pages/adm_dash.html")

# func usr_dashboard
@bp.route('/user_dashboard', methods=['GET', 'POST'])
def usr_dashboard():
    auth = ('User Manager', 'Group Manager', 'Auditor', 'External User')
# User Manager Group Manager Auditor Helpdesk Support Developer External User
    if session['role'] not in auth:
        return render_template("pages/no_access.html")

    form = ActionForm()
    if form.validate_on_submit():
        selected_option = form.action.data
        match selected_option:
            case 'C':
                return redirect(url_for('pages.create'))
            case 'R':
                return redirect(url_for('pages.select'))
            case 'U':
                return "<h1>Update</h1>"
            case 'D':
                return "<h1>Delete</h1>"

    return render_template("pages/usr_crud.html", form=form)

# func select
@bp.route("/select", methods=['GET', 'POST'])
def select():
    nw_conn = get_db_connection('northwind')
    nw_conn.autocommit = True                # Setting auto commit to True
    nw_cur = nw_conn.cursor()
    form = SelectForm()
    if form.validate_on_submit():
        uid = form.customer_id.data
        query = "SELECT * FROM customers WHERE customer_id = %s"
        print(query)
        nw_cur.execute(query, (uid,))
        result_set = nw_cur.fetchone()
        return render_template("pages/render_rs.html", data = result_set)

    return render_template("pages/select.html", form = form)

#func create
@bp.route("/create", methods=['GET', 'POST'])
def create():
    nw_conn = get_db_connection('northwind')
    nw_conn.autocommit = True                # Setting auto commit to True
    form = CRUD_Form()
    if request.method == 'POST':
        cur = nw_conn.cursor()
        sql = """INSERT INTO customers(customer_id
                           , company_name
                           , contact_name
                           , contact_title
                           , address
                           , city
                           , region
                           , postal_code
                           , country
                           , phone
                           , fax)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              """
        print (sql)
        record_to_insert = (str(form.customer_id.data),str(form.company_name.data),str(form.contact_name.data),str(form.contact_title.data),str(form.address.data),str(form.city.data),str(form.region.data),str(form.postal_code.data),str(form.country.data),str(form.phone_number.data),str(form.fax_number.data))
        cur.execute(sql, record_to_insert)

    return render_template("pages/create.html", form = form)

# func mgr_dashboard
@bp.route('/render_rs', methods=['GET', 'POST'])
def render():
    return render_template("pages/render_rs.html", form = form)

# func mgr_dashboard
@bp.route('/mgr_dashboard', methods=['GET', 'POST'])
def mgr_dashboard():
    auth = ('User Manager', 'Group Manager', 'Auditor')
# User Manager Group Manager Auditor Helpdesk Support Developer External User
    if session['role'] not in auth:
        return render_template("pages/no_access.html")
    q1 = """
      SELECT customer_id AS "Customer ID", COUNT(order_id) AS "Total Number of Orders"
      FROM orders
      WHERE order_date > '1996-12-31'
      GROUP BY customer_id
      HAVING COUNT(order_id) > 15
      ORDER BY "Total Number of Orders" DESC
    """
    q2 = """
      SELECT p.product_name AS "Product Name"
           , cast((SUM(o.unit_price * CAST(o.quantity AS FLOAT) * (1.0 - o.discount))) AS decimal(18,2)) AS "Total Sales"
      FROM products AS p
      INNER JOIN order_details AS o
      ON o.product_id = p.product_id
      GROUP BY p.product_name
      ORDER BY "Total Sales" DESC
      LIMIT 10
    """
    q3 = """
      SELECT e.city AS "City"
           , COUNT(DISTINCT e.employee_id) AS "Number of Employees"
           , COUNT(DISTINCT c.customer_id) AS "Number of Customers"
      FROM employees e
        LEFT JOIN customers c ON e.city = c.city
      GROUP BY e.city
      ORDER BY 2 DESC, 3
    """
    q4 = """
      WITH order_subtotals (customer_id, company_name, country, order_date, order_id, "Payments" ) AS (
        SELECT customers.customer_id
             , customers.company_name
             , customers.country
             , EXTRACT(YEAR FROM order_date) as order_date
             , orders.order_id
             , SUM(order_details.unit_price * CAST(order_details.quantity AS FLOAT) * (1.0- order_details.discount)) AS "Payments"
        FROM customers
        INNER JOIN orders ON orders.customer_id = customers.customer_id
        INNER JOIN order_details ON order_details.order_id = orders.order_id
        GROUP BY customers.customer_id
               , customers.company_name
               , customers.country
               , orders.order_date
               , orders.order_id
        ORDER BY customers.customer_id, orders.order_id
      ), details AS (SELECT customer_id
                          , order_date
                          , SUM("Payments") AS Total_Payed
                          , case when order_date = '1996' THEN SUM("Payments") END AS Payed_in_1996
                          , case when order_date = '1997' THEN SUM("Payments") END AS Payed_in_1997
                          , case when order_date = '1998' THEN SUM("Payments") END AS Payed_in_1998
                     FROM order_subtotals
                     GROUP BY customer_id, order_date
                     ORDER BY customer_id, order_date
                    ) SELECT customer_id
                           , CAST (sum(total_payed)AS INT) AS "Total Payed"
                           , IFNULL(CAST (SUM(Payed_in_1996) AS INT), 0) AS "1996"
                           , IFNULL(CAST (SUM(Payed_in_1997) AS INT), 0) AS "1997"
                           , IFNULL(CAST (SUM(Payed_in_1998) AS INT), 0) AS "1998"
                      FROM details
                      GROUP BY customer_id
                      ORDER BY "Total Payed" DESC
                      LIMIT 10
    """
    nw_conn = get_db_connection('northwind')
    nw_conn.autocommit = True                # Setting auto commit to True
    nw_cur = nw_conn.cursor()
    nw_cur.execute(q1)
    print(q1)
    # Create a DataFrame from the results
    df1 = pd.DataFrame(nw_cur.fetchall(), columns=[desc[0] for desc in nw_cur.description])
    nw_cur.execute(q2)
    print(q2)
    df2 = pd.DataFrame(nw_cur.fetchall(), columns=[desc[0] for desc in nw_cur.description])
    nw_cur.execute(q3)
    print(q3)
    df3 = pd.DataFrame(nw_cur.fetchall(), columns=[desc[0] for desc in nw_cur.description])
    nw_cur.execute(q4)
    print(q4)
    df4 = pd.DataFrame(nw_cur.fetchall(), columns=[desc[0] for desc in nw_cur.description])
    return render_template("pages/mgr_dash.html", d1=df1.to_html(index=False)
                                                , d2=df2.to_html(index=False)
                                                , d3=df3.to_html(index=False)
                                                , d4=df4.to_html(index=False))

@bp.route("/about", methods=['GET', 'POST'])
def about():
    return render_template("pages/about.html")

@bp.route("/logout", methods=['GET', 'POST'])
def logout():
    session['username'] = None
    session['role'] = None
    return render_template("pages/logout.html")
