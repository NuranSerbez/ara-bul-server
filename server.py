from flask import Flask, jsonify, request
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
engine = create_engine('postgresql://postgres:postgres@localhost/arabul')
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Define User model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

Base.metadata.create_all(engine)

# Endpoint for user registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    new_user = User(first_name=data['first_name'], last_name=data['last_name'], email=data['email'])
    new_user.set_password(data['password'])

    session = Session()
    try:
        session.add(new_user)
        session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except IntegrityError:
        session.rollback()
        return jsonify({'error': 'Email already exists'}), 400
    finally:
        session.close()

# Endpoint for user login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    session = Session()
    user = session.query(User).filter_by(email=email).first()

    if user and user.check_password(password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid email or password'}), 401
    

if __name__ == '__main__':
    app.run(debug=True)
