from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Orden, Usuario

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = '123456'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# -------- CREAR BD --------
with app.app_context():
    db.create_all()

# -------- LOGIN MANAGER --------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# -------- LOGIN --------
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = Usuario.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            error = "Usuario o contraseña incorrectos"

    return render_template('login.html', error=error)


# -------- REGISTRO --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Debe completar todos los campos")
            return redirect(url_for('register'))

        if Usuario.query.filter_by(username=username).first():
            flash("El usuario ya existe")
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)

        user = Usuario(username=username, password=hashed)
        db.session.add(user)
        db.session.commit()

        flash("Usuario registrado con éxito")
        return redirect(url_for('login'))

    return render_template('register.html')


# -------- DASHBOARD --------
@app.route('/dashboard')
@login_required
def dashboard():
    q = request.args.get('q', '').strip()

    if q:
        ordenes = Orden.query.filter(
            (Orden.cliente.contains(q)) |
            (Orden.equipo.contains(q)) |
            (Orden.estado.contains(q))
        ).order_by(Orden.id.desc()).all()
    else:
        ordenes = Orden.query.order_by(Orden.id.desc()).all()

    return render_template('dashboard.html', ordenes=ordenes, q=q)


# -------- NUEVA ORDEN --------
@app.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva_orden():
    if request.method == 'POST':

        fecha = request.form.get('fecha', '').strip()
        cliente = request.form.get('cliente', '').strip()
        contacto = request.form.get('contacto', '').strip()
        equipo = request.form.get('equipo', '').strip()
        marca = request.form.get('marca', '').strip()
        modelo = request.form.get('modelo', '').strip()
        falla = request.form.get('falla', '').strip()
        diagnostico = request.form.get('diagnostico', '').strip()
        trabajo = request.form.get('trabajo', '').strip()
        estado = request.form.get('estado', 'Pendiente').strip()

        if not fecha or not cliente or not equipo or not diagnostico:
            flash("Por favor completa todos los campos obligatorios")
            return redirect(url_for('nueva_orden'))

        orden = Orden(
            fecha=fecha,
            cliente=cliente,
            contacto=contacto,
            equipo=equipo,
            marca=marca,
            modelo=modelo,
            falla=falla,
            diagnostico=diagnostico,
            trabajo=trabajo,
            estado=estado
        )

        db.session.add(orden)
        db.session.commit()
        flash("Orden registrada con éxito")

        return redirect(url_for('dashboard'))

    return render_template('nueva_orden.html')


# -------- EDITAR ORDEN --------
@app.route('/editar/<int:orden_id>', methods=['GET', 'POST'])
@login_required
def editar_orden(orden_id):
    orden = Orden.query.get_or_404(orden_id)

    if request.method == 'POST':

        orden.fecha = request.form.get('fecha', '').strip()
        orden.cliente = request.form.get('cliente', '').strip()
        orden.contacto = request.form.get('contacto', '').strip()
        orden.equipo = request.form.get('equipo', '').strip()
        orden.marca = request.form.get('marca', '').strip()
        orden.modelo = request.form.get('modelo', '').strip()
        orden.falla = request.form.get('falla', '').strip()
        orden.diagnostico = request.form.get('diagnostico', '').strip()
        orden.trabajo = request.form.get('trabajo', '').strip()
        orden.estado = request.form.get('estado', 'Pendiente').strip()

        if not orden.fecha or not orden.cliente or not orden.equipo or not orden.diagnostico:
            flash("Por favor completa todos los campos obligatorios")
            return redirect(url_for('editar_orden', orden_id=orden_id))

        db.session.commit()
        flash("Orden actualizada con éxito")

        return redirect(url_for('dashboard'))

    return render_template('editar_orden.html', orden=orden)


# -------- ELIMINAR ORDEN --------
@app.route('/eliminar/<int:orden_id>', methods=['POST'])
@login_required
def eliminar_orden(orden_id):
    orden = Orden.query.get_or_404(orden_id)
    db.session.delete(orden)
    db.session.commit()
    flash("Orden eliminada correctamente")
    return redirect(url_for('dashboard'))


# -------- CAMBIAR ESTADO --------
@app.route('/estado/<int:orden_id>/<nuevo_estado>')
@login_required
def cambiar_estado(orden_id, nuevo_estado):
    orden = Orden.query.get_or_404(orden_id)
    orden.estado = nuevo_estado
    db.session.commit()
    flash("Estado actualizado")
    return redirect(url_for('dashboard'))


# -------- LOGOUT --------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
