from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Orden, Usuario
import os

app = Flask(__name__)

# ---------------- CONFIGURACIÓN BD ----------------
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SECRET_KEY'] = '123456'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# -------- CREAR BD Y ADMIN (SEGURO) --------
with app.app_context():
    db.create_all()

    admin = Usuario.query.filter_by(username='admin').first()
    if not admin:
        admin = Usuario(
            username='admin',
            password=generate_password_hash('admin123'),
            rol='admin'
        )
        db.session.add(admin)
        db.session.commit()


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
            if user.rol == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('tecnico_dashboard'))
        else:
            error = "Usuario o contraseña incorrectos"

    return render_template('login.html', error=error)

# ============================
#        DASHBOARDS
# ============================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.rol != 'admin':
        flash("Acceso no autorizado")
        return redirect(url_for('login'))

    q = request.args.get('q', '').strip()
    query = Orden.query

    if q:
        query = query.filter(
            (Orden.cliente.contains(q)) |
            (Orden.equipo.contains(q)) |
            (Orden.estado.contains(q))
        )

    ordenes = query.order_by(Orden.id.desc()).all()
    return render_template('dashboard_admin.html', ordenes=ordenes, q=q)

@app.route('/tecnico/dashboard')
@login_required
def tecnico_dashboard():
    if current_user.rol != 'tecnico':
        flash("Acceso no autorizado")
        return redirect(url_for('login'))

    q = request.args.get('q', '').strip()
    query = Orden.query.filter_by(tecnico_id=current_user.id)

    if q:
        query = query.filter(
            (Orden.cliente.contains(q)) |
            (Orden.equipo.contains(q)) |
            (Orden.estado.contains(q))
        )

    ordenes = query.order_by(Orden.id.desc()).all()
    return render_template('dashboard_tecnico.html', ordenes=ordenes, q=q)

# -------- NUEVA ORDEN --------
@app.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva_orden():

    tecnicos = []
    if current_user.rol == 'admin':
        tecnicos = Usuario.query.filter_by(rol='tecnico').all()

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

        if current_user.rol == 'admin':
            tecnico_id = request.form.get('tecnico_id')
        else:
            tecnico_id = current_user.id

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
            estado=estado,
            tecnico_id=tecnico_id
        )

        db.session.add(orden)
        db.session.commit()

        flash("Orden registrada con éxito")

        if current_user.rol == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('tecnico_dashboard'))

    return render_template('nueva_orden.html', tecnicos=tecnicos)

# -------- EDITAR ORDEN --------
@app.route('/editar/<int:orden_id>', methods=['GET', 'POST'])
@login_required
def editar_orden(orden_id):
    orden = Orden.query.get_or_404(orden_id)

    if current_user.rol != 'admin' and orden.tecnico_id != current_user.id:
        flash("No tienes permiso para editar esta orden")
        return redirect(url_for('tecnico_dashboard'))

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

        if current_user.rol == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('tecnico_dashboard'))

    return render_template('editar_orden.html', orden=orden)

# -------- ELIMINAR ORDEN --------
@app.route('/eliminar/<int:orden_id>', methods=['POST'])
@login_required
def eliminar_orden(orden_id):
    if current_user.rol != 'admin':
        flash("Solo el administrador puede eliminar órdenes")
        return redirect(url_for('tecnico_dashboard'))

    orden = Orden.query.get_or_404(orden_id)
    db.session.delete(orden)
    db.session.commit()

    flash("Orden eliminada correctamente")
    return redirect(url_for('admin_dashboard'))

# -------- CAMBIAR ESTADO --------
@app.route('/estado/<int:orden_id>/<nuevo_estado>')
@login_required
def cambiar_estado(orden_id, nuevo_estado):
    orden = Orden.query.get_or_404(orden_id)

    if current_user.rol != 'admin' and orden.tecnico_id != current_user.id:
        flash("No tienes permiso para cambiar el estado")
        return redirect(url_for('tecnico_dashboard'))

    orden.estado = nuevo_estado
    db.session.commit()
    flash("Estado actualizado")

    if current_user.rol == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('tecnico_dashboard'))

# -------- CREAR TÉCNICO --------
@app.route('/admin/crear_tecnico', methods=['GET', 'POST'])
@login_required
def crear_tecnico():
    if current_user.rol != 'admin':
        flash("Acceso no autorizado")
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Debe completar todos los campos")
            return redirect(url_for('crear_tecnico'))

        if Usuario.query.filter_by(username=username).first():
            flash("El usuario ya existe")
            return redirect(url_for('crear_tecnico'))

        hashed = generate_password_hash(password)
        tecnico = Usuario(username=username, password=hashed, rol='tecnico')

        db.session.add(tecnico)
        db.session.commit()

        flash("Técnico creado correctamente")
        return redirect(url_for('admin_dashboard'))

    return render_template('crear_tecnico.html')

# -------- LOGOUT --------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
