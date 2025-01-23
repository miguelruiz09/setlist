
import streamlit as st
import sqlite3
import bcrypt
from datetime import datetime
import json

def hash_password(password):
    """Hashear contraseña de forma segura"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt)

def verify_password(stored_password, provided_password):
    """Verificar contraseña contra hash almacenado"""
    # Asegurar que stored_password sea bytes
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')
    
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)

def init_database():
    """Inicializar base de datos con tablas y usuarios por defecto"""
    try:
        conn = sqlite3.connect('setlist_helper.db')
        c = conn.cursor()
        
        # Crear tablas
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )''')
        
        # Verificar si ya existen usuarios
        c.execute('SELECT * FROM users WHERE username = ?', ("admin",))
        if not c.fetchone():
            # Crear usuarios con contraseñas hasheadas correctamente
            admin_pass = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
            c.execute('''
                INSERT INTO users (username, password, role) 
                VALUES (?, ?, ?)
            ''', ("admin", admin_pass, "admin"))
            
            user_pass = bcrypt.hashpw("user123".encode(), bcrypt.gensalt())
            c.execute('''
                INSERT INTO users (username, password, role) 
                VALUES (?, ?, ?)
            ''', ("usuario", user_pass, "user"))
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error de inicialización de base de datos: {e}")
    finally:
        conn.close()

def login_user(username, password):
    """Autenticar usuario"""
    try:
        conn = sqlite3.connect('setlist_helper.db')
        c = conn.cursor()
        
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        
        if user:
            if verify_password(user[2], password):
                return {
                    "id": user[0],
                    "username": user[1],
                    "role": user[3]
                }
        return None
    except sqlite3.Error as e:
        print(f"Error de inicio de sesión: {e}")
        return None
    finally:
        conn.close()
        
def login_page():
    """Página de inicio de sesión"""
    st.title("SetList Helper 🎵")
    
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Iniciar Sesión"):
        user = login_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.experimental_rerun()
        else:
            st.error("Credenciales incorrectas")

def main():
    init_database()
    
    # Inicializar estado de sesión
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.current_song = None
    
    # Lógica de navegación
    if not st.session_state.logged_in:
        login_page()
    else:
        # Menú de navegación para usuarios logueados
        st.sidebar.title(f"Bienvenido, {st.session_state.user['username']}")
        options = ["Inicio"]
        
        if st.session_state.user['role'] == 'admin':
            options.extend(["Gestionar Canciones", "Gestionar SetLists"])
        
        options.extend(["Mis SetLists", "Cerrar Sesión"])
        choice = st.sidebar.radio("Menú", options)
        
        # Resto del código de navegación
        if choice == "Inicio":
            st.title("SetList Helper 🎵")
            st.markdown("""
            ## Bienvenido a la aplicación de gestión de SetLists
            - Crea y gestiona tus SetLists musicales
            - Guarda canciones con detalles personalizados
            - Organiza tus repertorios
            """)
        elif choice == "Gestionar Canciones":
            manage_songs_page()
        elif choice == "Mis SetLists":
            show_setlists_page()
        elif choice == "Cerrar Sesión":
            st.session_state.logged_in = False
            st.session_state.user = None
            st.experimental_rerun()

def manage_songs_page():
    """Página de gestión de canciones para admin"""
    st.title("Gestionar Canciones")
    
    # Formulario para agregar canción
    with st.form("add_song_form"):
        title = st.text_input("Título de la Canción")
        key = st.text_input("Clave Musical")
        duration = st.number_input("Duración (minutos)", min_value=0)
        notes = st.text_area("Notas Adicionales")
        
        submit = st.form_submit_button("Agregar Canción")
        
        if submit:
            try:
                conn = sqlite3.connect('setlist_helper.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO songs (title, key, duration, notes)
                    VALUES (?, ?, ?, ?)
                ''', (title, key, duration, notes))
                conn.commit()
                st.success("Canción agregada exitosamente!")
            except sqlite3.Error as e:
                st.error(f"Error al agregar canción: {e}")
            finally:
                conn.close()
    
    # Mostrar canciones existentes
    songs = get_all_songs()
    if songs:
        st.subheader("Canciones Existentes")
        for song in songs:
            col1, col2 = st.columns([4,1])
            with col1:
                st.write(f"{song['title']} ({song['key']})")
            with col2:
                if st.button(f"Eliminar {song['id']}", key=f"del_song_{song['id']}"):
                    try:
                        conn = sqlite3.connect('setlist_helper.db')
                        c = conn.cursor()
                        c.execute('DELETE FROM songs WHERE id = ?', (song['id'],))
                        conn.commit()
                        st.success("Canción eliminada!")
                        st.rerun()
                    except sqlite3.Error as e:
                        st.error(f"Error al eliminar canción: {e}")
                    finally:
                        conn.close()

def show_setlists_page():
    """Página para mostrar y crear SetLists"""
    st.title("Mis SetLists")
    
    songs = get_all_songs()
    with st.form("setlist_form"):
        setlist_name = st.text_input("Nombre del SetList")
        setlist_date = st.date_input("Fecha del SetList", datetime.now())
        
        available_songs = {f"{song['id']}. {song['title']} ({song['key']})": song 
                         for song in songs}
        
        selected_songs = st.multiselect(
            "Selecciona y ordena las canciones",
            options=list(available_songs.keys())
        )
        
        submitted = st.form_submit_button("Crear SetList")
        
        if submitted and setlist_name and selected_songs:
            songs_for_setlist = [available_songs[song] for song in selected_songs]
            save_setlist(
                setlist_name,
                setlist_date.strftime("%Y-%m-%d"),
                songs_for_setlist
            )
            st.success("SetList creado!")
    
    # Mostrar SetLists existentes
    setlists = get_all_setlists()
    if setlists:
        st.subheader("SetLists Guardados")
        for setlist in setlists:
            col1, col2 = st.columns([4,1])
            with col1:
                with st.expander(f"{setlist['name']} - {setlist['date']}"):
                    for song in setlist['songs']:
                        st.write(f"{song['title']} ({song['key']})")
            with col2:
                if st.button("Eliminar", key=f"del_setlist_{setlist['id']}"):
                    delete_setlist(setlist['id'])
                    st.success("SetList eliminado!")
                    st.rerun()

def get_all_songs():
    """Obtener todas las canciones"""
    try:
        conn = sqlite3.connect('setlist_helper.db')
        c = conn.cursor()
        c.execute('SELECT * FROM songs')
        columns = ['id', 'title', 'key', 'duration', 'notes']
        return [dict(zip(columns, row)) for row in c.fetchall()]
    except sqlite3.Error as e:
        st.error(f"Error al recuperar canciones: {e}")
        return []
    finally:
        conn.close()

def save_setlist(name, date, songs):
    """Guardar un nuevo SetList"""
    try:
        conn = sqlite3.connect('setlist_helper.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO setlists (user_id, name, date, songs) 
            VALUES (?, ?, ?, ?)
        ''', (
            st.session_state.user['id'], 
            name, 
            date, 
            json.dumps(songs)
        ))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error al guardar SetList: {e}")
    finally:
        conn.close()

def get_all_setlists():
    """Obtener todos los SetLists del usuario actual"""
    try:
        conn = sqlite3.connect('setlist_helper.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT id, name, date, songs 
            FROM setlists 
            WHERE user_id = ?
        ''', (st.session_state.user['id'],))
        
        setlists = []
        for row in c.fetchall():
            setlist = {
                'id': row[0],
                'name': row[1],
                'date': row[2],
                'songs': json.loads(row[3])
            }
            setlists.append(setlist)
        
        return setlists
    except sqlite3.Error as e:
        st.error(f"Error al recuperar SetLists: {e}")
        return []
    finally:
        conn.close()

def delete_setlist(setlist_id):
    """Eliminar un SetList específico"""
    try:
        conn = sqlite3.connect('setlist_helper.db')
        c = conn.cursor()
        
        c.execute('DELETE FROM setlists WHERE id = ?', (setlist_id,))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error al eliminar SetList: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
