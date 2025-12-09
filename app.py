from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_pymongo import PyMongo
from flask_session import Session
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import os
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
Session(app)

mongo = PyMongo(app)

# Create upload folder if missing
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# ----------------- User Routes -----------------

@app.route('/')
def index():
    search = request.args.get('search','')
    category = request.args.get('category','')
    query = {}
    if search:
        query['title'] = {'$regex': search,'$options':'i'}
    if category:
        query['category'] = category
    products = list(mongo.db.products.find(query))
    return render_template('index.html', products=products, search=search, category=category)

@app.route('/product/<pid>')
def product_detail(pid):
    product = mongo.db.products.find_one({'_id': ObjectId(pid)})
    return render_template('product.html', product=product)

@app.route('/cart')
def cart():
    user_cart = session.get('cart', [])
    cart_items=[]
    total=0
    for item in user_cart:
        prod = mongo.db.products.find_one({'_id': ObjectId(item['product_id'])})
        if prod:
            subtotal = prod['price']*item['qty']
            total+=subtotal
            cart_items.append({'product':prod,'qty':item['qty'],'subtotal':subtotal})
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/cart/add/<pid>')
def add_to_cart(pid):
    cart = session.get('cart', [])
    for item in cart:
        if item['product_id']==pid:
            item['qty']+=1
            session['cart']=cart
            return redirect(url_for('cart'))
    cart.append({'product_id':pid,'qty':1})
    session['cart']=cart
    return redirect(url_for('cart'))

@app.route('/cart/update',methods=['POST'])
def update_cart():
    cart=[]
    for pid, qty in request.form.items():
        cart.append({'product_id':pid,'qty':int(qty)})
    session['cart']=cart
    return redirect(url_for('cart'))

@app.route('/auth',methods=['GET','POST'])
def auth():
    if request.method=='POST':
        email=request.form.get('email')
        password=request.form.get('password')
        user = mongo.db.users.find_one({'email':email})
        if user and user['password']==password:
            session['user']=email
            return redirect(url_for('index'))
        return "Invalid credentials"
    return render_template('auth.html')

# ----------------- Admin Routes -----------------

@app.route('/admin-login',methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        user = request.form.get('user')
        pwd = request.form.get('pass')
        if user==app.config['ADMIN_USER'] and pwd==app.config['ADMIN_PASS']:
            session['admin']=True
            return redirect(url_for('admin_dashboard'))
        return "Invalid admin credentials"
    return render_template('admin-login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    search=request.args.get('search','')
    query={}
    if search:
        query['title']={'$regex':search,'$options':'i'}
    products=list(mongo.db.products.find(query))
    return render_template('admin.html', products=products, search=search)

@app.route('/admin/create',methods=['POST'])
def admin_create():
    if not session.get('admin'):
        return jsonify({'error':'Not authorized'}),401
    title=request.form.get('title')
    desc=request.form.get('desc')
    price=float(request.form.get('price'))
    category=request.form.get('category')
    image_file=request.files.get('image')
    image_filename=None
    if image_file:
        filename=secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        image_filename=filename
    mongo.db.products.insert_one({'title':title,'desc':desc,'price':price,'category':category,'image':image_filename})
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<pid>',methods=['GET','POST'])
def admin_edit(pid):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    product=mongo.db.products.find_one({'_id':ObjectId(pid)})
    if request.method=='POST':
        title=request.form.get('title')
        desc=request.form.get('desc')
        price=float(request.form.get('price'))
        category=request.form.get('category')
        image_file=request.files.get('image')
        update_data={'title':title,'desc':desc,'price':price,'category':category}
        if image_file:
            filename=secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            update_data['image']=filename
        mongo.db.products.update_one({'_id':ObjectId(pid)},{'$set':update_data})
        return redirect(url_for('admin_dashboard'))
    return render_template('admin-edit.html', product=product)

@app.route('/admin/delete/<pid>')
def admin_delete(pid):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    mongo.db.products.delete_one({'_id':ObjectId(pid)})
    return redirect(url_for('admin_dashboard'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__=='__main__':
    app.run(debug=True)
