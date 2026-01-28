from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class Orden(db.Model):
    __tablename__ = 'ordenes'

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(20))
    cliente = db.Column(db.String(100))
    contacto = db.Column(db.String(50))
    equipo = db.Column(db.String(50))
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    falla = db.Column(db.Text)
    diagnostico = db.Column(db.Text)
    trabajo = db.Column(db.Text)
    estado = db.Column(db.String(30))


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
