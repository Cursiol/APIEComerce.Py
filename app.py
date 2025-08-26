#Importação da Biblioteca Flask
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

# Importação do módulo para manipulação de senhas
app = Flask(__name__)
app.config['SECRET_KEY'] = 'minha_chave_123' # Chave secreta para sessões
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'

login_manager = LoginManager()
db = SQLAlchemy(app)
login_manager.init_app(app)
login_manager.login_view = 'login'  # Define a rota de login
CORS(app)  # Habilita CORS para todas as rotas

#Modelagem
#Criação do Usuario (id, name, password)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    cart = db.relationship('CartItem', backref='user', lazy=True) #carrinho de compras do usuario

#Autenticação do usuario
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Fazer o login do usuario
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()

    if user and data.get('password') == user.password:
            login_user(user)
            return jsonify({'message': 'Logged in successfully'})
    
    return jsonify({'message': 'Unauthorized. Invalid credentials'}), 401
    
#Rota para logout do usuario
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successfully'})

#Produto (id, name, price, description)
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text())

#Carrinho de compras (id, user_id, product_id, quantity)
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)


#adicionar o produto ao banco de dados
@app.route('/api/products/add', methods=['POST'])
@login_required  # Protege a rota para que apenas usuários logados possam acessar
def add_product():
    data = request.json
    if 'name' in data and 'price' in data:
        product = Product(name=data['name'], price=data['price'], description=data.get('description', ''))
        db.session.add(product)
        db.session.commit()
        return jsonify({'Message': 'Product added successfully'}) 
    return jsonify({'Message': 'Invalid product data'}), 400

#deletar o produto do banco de dados
@app.route('/api/products/delete/<int:product_id>', methods=['DELETE'])
@login_required  # Protege a rota para que apenas usuários logados possam acessar
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product: 
        db.session.delete(product)
        db.session.commit()
        return jsonify({'Message': 'Product deleted successfully'})
    return jsonify({'Message': 'Product not found'}), 404

#Recuperar dados do produto
@app.route('/api/products/<int:product_id>', methods=['GET'])
def fet_product_details(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'description': product.description
        })
    return jsonify({'Message': 'Product not found'}), 404

#Atualizar dados do produto
@app.route('/api/products/update/<int:product_id>', methods=['PUT'])
@login_required  # Protege a rota para que apenas usuários logados possam acessar
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'Message': 'Product not found'}), 404

    data = request.json
    if 'name' in data:
        product.name = data['name']
    
    if 'price' in data:
        product.price = data['price']
    
    if 'description' in data:
        product.description = data['description']

    db.session.commit()
    return jsonify({'Message': 'Product update successfully'})

#Listar todos os produtos
@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    product_list = []
    print(products)
    for product in products:
        product_data = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
        }
        product_list.append(product_data)
    return jsonify(product_list)

#checkout do carrinho de compras
@app.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required # Protege a rota para que apenas usuários logados possam acessar
def add_to_cart(product_id):
    user = User.query.get(int(current_user.id))
    product = Product.query.get(product_id)

    if user and product:
        cart_item = CartItem(user_id=user.id, product_id=product.id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({'Message': 'Item added to the cart successfully'})
    
    return jsonify({'Message': 'Failed to add item to the cart'}), 404

# Remover item do carrinho de compras
@app.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
@login_required  # Protege a rota para que apenas usuários logados possam acessar
def remove_from_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'Message': 'Item removed from the cart successfully'})
    return jsonify({'Message': 'Failed to remove item from the cart'}), 400

#ver os itens do carrinho de compras
@app.route('/api/cart', methods=['GET'])
@login_required  # Protege a rota para que apenas usuários logados possam acessar
def view_cart():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart
    cart_content = []
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        cart_content.append({
                        'id': cart_item.id,
                        'user_id': cart_item.user_id,
                        'product_id': cart_item.product_id,
                        'product_name': product.name,
                        'product_price': product.price
                     })
    return jsonify(cart_content)

#limpar o carrinho de compras
@app.route('/api/cart/checkout', methods=['POST'])
@login_required  # Protege a rota para que apenas usuários logados possam acessar
def checkout():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart
    for cart_item in cart_items:
        db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'Message': 'Checkout successful. Cart has been cleared.'})

if __name__ == '__main__':
    app.run(debug=True)