from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from flask_mail import Mail, Message
import mysql.connector
import random
import string

app = Flask(__name__)
app.secret_key = 'secret_hehe'

# ---------------------- Flask-Mail Config ----------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # your email provider
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'reybendelmundo2005@gmail.com'  # replace with your sending email
app.config['MAIL_PASSWORD'] = 'qrts tlxb hzzo zmqg'      # use Gmail App Password
mail = Mail(app)

# Temporary storage for OTPs
otp_storage = {}  # email -> otp

# ---------------------- DB Connection ----------------------
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='12345',
        database='inventorydb'
    )
    return conn


#----------------------ROUTES----------------------#
@app.route('/')
@app.route('/Welcome Page')
def welcome_page():
    return render_template('Welcome Page/index.html')

@app.route('/Login Form')
def login_form():
    # Show login page always, unless a session is clearly active and valid
    if session.get('user') and session.get('accrole') in ['Admin', 'Staff']:
        # Optional: verify session with DB to prevent stale login
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM registeredaccs WHERE email = %s", (session['user'],))
        user_exists = cursor.fetchone()
        conn.close()
        if user_exists:
            if session['accrole'] == 'Admin':
                return redirect('/Admin Account')
            elif session['accrole'] == 'Staff':
                return redirect('/Staff Account')
    # Otherwise, show login page
    return render_template('Login Form/index.html')


@app.route('/Admin Account')
def admin_account():
    if not session.get('user') or session.get('accrole') != 'Admin':
        flash('Please log in first.', 'danger')
        return redirect('/')
    return render_template('Admin Account/index.html')


@app.route('/Staff Account')
def staff_account():
    if not session.get('user') or session.get('accrole') != 'Staff':
        flash('Please log in first.', 'danger')
        return redirect('/')
    return render_template('Staff Account/index.html')


@app.route('/Account Register')
def admin_reg_account():
    return render_template('Login Form/account_register.html')


@app.route('/Medicine Tab')
def medicine_tab():
    if 'user' not in session:
        flash('Please log in first.', 'danger')
        return redirect('/')
    return render_template('Inventory/medicine.html')

@app.route('/Notif Tab')
def notif_tab():
    return render_template('Admin Account/Sidebar/notif.html')

@app.route('/History Tab')
def history_tab():
    return render_template('Admin Account/Sidebar/history.html')

@app.route('/Trash Tab')
def trash_tab():
    return render_template('Admin Account/Sidebar/trash.html')

@app.route('/Inventory Index')
def inventory_index():
    if 'user' not in session:
        flash('Please log in first.', 'danger')
        return redirect('/')
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM medicine")
    medicine = cursor.fetchall()
    conn.close()
    return render_template('Inventory/index.html', medicine=medicine)

@app.route('/Essential_Meds')
def ess_med():
    return render_template('Inventory/essential_meds.html')


@app.route('/terms')
def terms():
    return render_template('Terms and Privacy/terms.html')


@app.route('/privacy')
def privacy():
    return render_template('Terms and Privacy/privacy.html')


@app.route('/medicine/<category>')
def medicine_category(category):
    if 'user' not in session:
        flash('Please log in first.', 'danger')
        return redirect('/')
    
    categories = {
        'essential': 'Essential Medication',
        'protection': 'Personal Protection',
        'firstaid': 'First Aid Tool',
        'woundcare': 'Wound Care Items',
        'diagnostic': 'Diagnostic Tools',
        'others': 'Others'
    }

    if category not in categories:
        return "Category not found", 404

    return render_template(
        'Inventory/medicine_category.html', 
        category_name=categories[category],
        category_key=category
    )

@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.form.get('email')
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400

    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp

    msg = Message(
        subject="Your OTP Code",
        sender=app.config['MAIL_USERNAME'],
        recipients=[email],
        body=f"Your OTP code is: {otp}"
    )
    try:
        mail.send(msg)
        return jsonify({'status': 'success', 'message': 'OTP sent!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

#----------------------INVITE CODE----------------------#
def generate_invite_code(length=8):
    """Generate a random alphanumeric invite code"""
    letters_and_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))


@app.route('/generate_invite', methods=['GET'])
def generate_invite():
    if 'user' not in session or session.get('accrole') != 'Admin':
        flash('You are not authorized to access this page.', 'danger')
        return redirect('/')
        
    code = generate_invite_code()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO invite_codes (code, is_used) VALUES (%s, FALSE)", (code,))
    conn.commit()
    conn.close()
    
    return render_template('Admin Account/generate_invite.html', code=code)

@app.route('/add_item', methods=['POST', 'GET'])
def additem():

    ItemName = request.form.get('ItemName')
    Quantity = request.form.get('Quantity')
    rfid = request.form.get('RFIDNUM')
    Selections = request.form.get('Selections')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "INSERT INTO medrecords (ItemName, Quantity, RFIDNUM, Selections) VALUES (%s, %s, %s, %s)",
        (ItemName, Quantity, rfid, Selections)
    )
    conn.commit()
    conn.close()

    return redirect('/Staff Account')


#----------------------REGISTER ACCOUNT----------------------#
@app.route('/register', methods=['POST'])
def register():
    invite_code = request.form.get('invite_code')
    username = request.form.get('username')
    firstname = request.form.get('firstname')
    middlename = request.form.get('middlename')
    lastname = request.form.get('lastname')
    email = request.form.get('email')
    createpassword = request.form.get('createpassword')
    confirmpassword = request.form.get('accountpassword')
    role = request.form.get('accrole')
    phone = request.form.get('phone')
    birthdate = request.form.get('birthdate')
    address = request.form.get('address')
    otp_input = request.form.get('otp')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------------------- Check OTP ----------------------
    if otp_storage.get(email) != otp_input:
        flash('❌ Invalid OTP!', 'danger')
        return redirect('/Account Register')
    del otp_storage[email]  # remove OTP after use

    # ---------------------- Check username ----------------------
    cursor.execute("SELECT * FROM registeredaccs WHERE username = %s", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        flash('Username already exists', 'danger')
        conn.close()
        return redirect('/Account Register')

    # ---------------------- Check invite code ----------------------
    cursor.execute("SELECT * FROM invite_codes WHERE code = %s AND is_used = FALSE", (invite_code,))
    valid_code = cursor.fetchone()
    if not valid_code:
        flash('❌ Invalid or already used invite code.', 'danger')
        conn.close()
        return redirect('/Account Register')

    cursor.execute("UPDATE invite_codes SET is_used = TRUE WHERE code = %s", (invite_code,))

    # ---------------------- Password Validation ----------------------
    if createpassword != confirmpassword:
        flash('❌ Passwords do not match.', 'danger')
        conn.close()
        return redirect('/Account Register')

    # ---------------------- Insert into DB ----------------------
    cursor.execute("""
        INSERT INTO registeredaccs
        (username, firstname, middlename, lastname, email, accountpassword, accrole, phone, birthdate, address)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (username, firstname, middlename, lastname, email, createpassword, role, phone, birthdate, address))

    conn.commit()
    conn.close()
    flash('✅ Account created successfully!', 'success')
    return redirect('/')


#----------------------MEDICINE MANAGEMENT----------------------#
@app.route('/add', methods=['POST'])
def add_medicines():
    if 'user' not in session:
        flash('Please log in first.', 'danger')
        return redirect('/')
        
    GenName = request.form['MedGenName']
    BrandName = request.form['BrandName']
    Type = request.form['MedType']
    AdultOrKids = request.form['AdultOrKids']
    Variant = request.form['MedVariant']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO medicine (MedGenName, BrandName, MedType, AdultOrKids, MedVariant) VALUES (%s, %s, %s, %s, %s)",
        (GenName, BrandName, Type, AdultOrKids, Variant)
    )
    conn.commit()
    conn.close()
    
    flash('Medicine successfully added!', 'success')
    return redirect('/Inventory Index')


@app.route('/delete_all', methods=['POST'])
def delete_all_medicines():
    if 'user' not in session:
        flash('Please log in first.', 'danger')
        return redirect('/')
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM medicine")
    cursor.execute("ALTER TABLE medicine AUTO_INCREMENT = 1")
    conn.commit()
    conn.close()
    flash('All medicines deleted successfully!', 'success')
    return redirect('/Inventory Index')


#----------------------LOGIN----------------------#
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['accountpassword']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM registeredaccs WHERE email = %s AND accountpassword = %s", (email, password))
    user = cursor.fetchone()

    conn.close()

    if user:
        session['user'] = user['email']
        session['accrole'] = user['accrole']
        flash('Login successful!', 'success')

        # Redirect by role
        if user['accrole'] == 'Admin':
            return redirect('/Admin Account')
        elif user['accrole'] == 'Staff':
            return redirect('/Staff Account')
    else:
        flash('Invalid email or password. Please try again.', 'danger')
        return redirect('/')


#----------------------LOG OUT----------------------#
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect('/')


#----------------------FOR BROWSER SESSION HANDLER----------------------#
@app.after_request
def add_header(response):
    # Prevent browser from caching any pages
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


#----------------------RUN APP----------------------#
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
