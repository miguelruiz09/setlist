import bcrypt
import os
import streamlit as st
import sqlite3
from datetime import datetime
import json
import gc

def restore():
    gc.collect()
    if os.path.exists('setlist3.db'):
        try:
            os.remove('setlist3.db')
        except PermissionError as e:
            print(f"Error al intentar eliminar la base de datos: {e}")

def reset_database():
    restore()
    conn = sqlite3.connect('setlist3.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        tempo TEXT,
        key TEXT,
        notes TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS setlists (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        name TEXT NOT NULL,
        date TEXT,
        songs TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    try:
        c.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("admin",))
        if c.fetchone()[0] == 0:
            admin_pass = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
            c.execute('''
                INSERT INTO users (username, password, role) 
                VALUES (?, ?, ?)
            ''', ("admin", admin_pass, "admin"))
        
        c.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("usuario",))
        if c.fetchone()[0] == 0:
            user_pass = bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt())
            c.execute('''
                INSERT INTO users (username, password, role) 
                VALUES (?, ?, ?)
            ''', ("usuario", user_pass, "user"))
    except sqlite3.Error as e:
        st.error(f"Error al insertar usuarios: {e}")
    
    conn.commit()
    conn.close()

def verify_password(stored_password, provided_password):
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)

def login_user(username, password):
    try:
        conn = sqlite3.connect('setlist3.db')
        c = conn.cursor()
        
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        
        if user and verify_password(user[2], password):
            return {
                "id": user[0],
                "username": user[1],
                "role": user[3]
            }
        return None
    except sqlite3.Error as e:
        st.error(f"Error de inicio de sesión: {e}")
        return None
    finally:
        conn.close()

def login_page():
    st.title("SetList IDJ Cali 🎵")
    
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Iniciar Sesión"):
        user = login_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

def get_all_songs():
    try:
        conn = sqlite3.connect('setlist3.db')
        c = conn.cursor()
        c.execute('SELECT * FROM songs')
        columns = ['id', 'title', 'key', 'notes']
        return [dict(zip(columns, row)) for row in c.fetchall()]
    except sqlite3.Error as e:
        st.error(f"Error al recuperar canciones: {e}")
        return []
    finally:
        conn.close()

def save_setlist(name, date, songs):
    try:
        conn = sqlite3.connect('setlist3.db')
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
    try:
        conn = sqlite3.connect('setlist3.db')
        c = conn.cursor()
        
        # Mostrar todos los setlists, no solo los del usuario logueado
        c.execute('''SELECT id, user_id, name, date, songs FROM setlists''')
        
        setlists = []
        for row in c.fetchall():
            setlist = {
                'id': row[0],
                'user_id': row[1],
                'name': row[2],
                'date': row[3],
                'songs': json.loads(row[4])
            }
            setlists.append(setlist)
        
        return setlists
    except sqlite3.Error as e:
        st.error(f"Error al recuperar SetLists: {e}")
        return []
    finally:
        conn.close()

def delete_setlist(setlist_id):
    try:
        conn = sqlite3.connect('setlist3.db')
        c = conn.cursor()
       
        c.execute('DELETE FROM setlists WHERE id = ?', (setlist_id,))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error al eliminar SetList: {e}")
    finally:
        conn.close()

def manage_songs_page():
    st.title("Gestionar Canciones")
    
    if 'editing_song' not in st.session_state:
        st.session_state.editing_song = None

    with st.form("song_form", clear_on_submit=True):
        if st.session_state.editing_song:
            song = st.session_state.editing_song
            title = st.text_input("Título de la Canción", value=song['title'])
            key = st.text_input("Tono", value=song.get('key', ''))
            tempo = st.text_input("Tempo", value=song.get('tempo', ''))
            notes = st.text_area("Acordes", value=song.get('notes', ''))
        else:
            title = st.text_input("Título de la Canción")
            key = st.text_input("Tono")
            tempo = st.text_input("Tempo")
            notes = st.text_area("Acordes")

        submit = st.form_submit_button("Guardar Canción")
        
        if submit:
            try:
                conn = sqlite3.connect('setlist3.db')
                c = conn.cursor()
                
                if st.session_state.editing_song:
                    c.execute('''
                        UPDATE songs 
                        SET title = ?, key = ?, tempo = ?, notes = ? 
                        WHERE id = ?
                    ''', (title, key, tempo, notes, st.session_state.editing_song['id']))
                    st.success("Canción actualizada exitosamente!")
                    st.session_state.editing_song = None
                else:
                    c.execute('''
                        INSERT INTO songs (title, key, tempo, notes)
                        VALUES (?, ?, ?, ?)
                    ''', (title, key, tempo, notes))
                    st.success("Canción agregada exitosamente!")
                
                conn.commit()
            except sqlite3.Error as e:
                st.error(f"Error al guardar canción: {e}")
            finally:
                conn.close()
    
    search_term = st.text_input("Buscar canciones...")

    songs = get_all_songs()
    filtered_songs = [
        song for song in songs 
        if search_term.lower() in song['title'].lower() 
        or search_term.lower() in song.get('key', '').lower()
    ]
    
    songs_per_page = 5
    total_songs = len(filtered_songs)
    total_pages = max(1, (total_songs - 1) // songs_per_page + 1)
    
    current_page = st.number_input(
        "Página", 
        min_value=1, 
        max_value=total_pages, 
        value=1
    ) - 1
    
    start_idx = current_page * songs_per_page
    end_idx = start_idx + songs_per_page
    page_songs = filtered_songs[start_idx:end_idx]
    
    if page_songs:
        st.subheader(f"Canciones Existentes (Página {current_page + 1} de {total_pages})")
        for song in page_songs:
            col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
            with col1:
                st.write(f"{song['title']} ({song.get('key', 'Sin clave')})")
            with col2:
                if st.session_state.user['role'] == 'admin' and st.button("Editar", key=f"edit_song_{song['id']}"):
                    st.session_state.editing_song = song
                    st.rerun()
            with col3:
                if st.session_state.user['role'] == 'admin' and st.button("Eliminar", key=f"del_song_{song['id']}"):
                    try:
                        conn = sqlite3.connect('setlist3.db')
                        c = conn.cursor()
                        c.execute('DELETE FROM songs WHERE id = ?', (song['id'],))
                        conn.commit()
                        st.success("Canción eliminada!")
                        st.rerun()
                    except sqlite3.Error as e:
                        st.error(f"Error al eliminar canción: {e}")
                    finally:
                        conn.close()
            with col4:
                if st.button("Ver Notas", key=f"view_notes_song_{song['id']}"):
                    st.session_state.previous_page = st.session_state.current_page
                    st.session_state.current_page = "View Notes"
                    st.session_state.selected_song = song
                    st.rerun()
        
        st.write(f"Total de canciones: {total_songs}")
    else:
        st.write("No se encontraron canciones.")

def show_setlists_page():
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

    setlists = get_all_setlists()
    if setlists:
        st.subheader("SetLists Guardados")
        for setlist in setlists:
            col1, col2 = st.columns([4, 1])
            with col1:
                with st.expander(f"{setlist['name']} - {setlist['date']}"):
                    for song in setlist['songs']:
                        st.write(f"{song['title']} ({song['key']})")

                        # Aquí cambiamos el key para que sea único, agregando el ID de la canción
                        if st.button("Ver Notas", key=f"view_notes_song_{song['id']}"):
                            st.session_state.previous_page = st.session_state.current_page
                            st.session_state.current_page = "View Notes"
                            st.session_state.selected_song = song
                            st.rerun()
            with col2:
                if st.session_state.user['role'] == 'admin' and st.button("Eliminar", key=f"del_setlist_{setlist['id']}"):
                    delete_setlist(setlist['id'])
                    st.success("SetList eliminado!")
                    st.rerun()


def change_password(user_id, current_password, new_password):
    try:
        conn = sqlite3.connect('setlist3.db')
        c = conn.cursor()
        
        # Verify current password
        c.execute('SELECT password FROM users WHERE id = ?', (user_id,))
        stored_password = c.fetchone()[0]
        
        if not verify_password(stored_password, current_password):
            return False, "La contraseña actual es incorrecta"
        
        # Hash and update new password
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        c.execute('UPDATE users SET password = ? WHERE id = ?', (new_password_hash, user_id))
        conn.commit()
        return True, "Contraseña actualizada exitosamente"
    except sqlite3.Error as e:
        return False, f"Error al cambiar la contraseña: {e}"
    finally:
        conn.close()

def change_password_page():
    st.title("Cambiar Contraseña")
    
    current_password = st.text_input("Contraseña Actual", type="password")
    new_password = st.text_input("Nueva Contraseña", type="password")
    confirm_password = st.text_input("Confirmar Nueva Contraseña", type="password")
    
    if st.button("Cambiar Contraseña"):
        if new_password != confirm_password:
            st.error("Las nuevas contraseñas no coinciden")
        elif len(new_password) < 6:
            st.error("La nueva contraseña debe tener al menos 6 caracteres")
        else:
            success, message = change_password(st.session_state.user['id'], current_password, new_password)
            if success:
                st.success(message)
            else:
                st.error(message)

def main():
    if not os.path.exists('setlist3.db'):
        reset_database()

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None

    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Mis SetLists"  # Cambié aquí para evitar la página de inicio.

    if 'selected_song' not in st.session_state:
        st.session_state.selected_song = None

    if 'previous_page' not in st.session_state:
        st.session_state.previous_page = None

    if not st.session_state.logged_in:
        login_page()
    else:
        # Si la página actual es "View Notes" y hay una canción seleccionada, se muestra la vista de notas
        if st.session_state.current_page == "View Notes" and st.session_state.selected_song:
            view_notes_page()
        else:
            # Guarda la página actual antes de cambiar
            previous_page = st.session_state.current_page
            
            st.sidebar.title(f"Bienvenido, {st.session_state.user['username']}")
            options = ["Mis SetLists", "Gestionar Canciones", "Cambiar Contraseña", "Cerrar Sesión"]
            choice = st.sidebar.radio("Menú", options)

            # Si la opción cambia, actualizamos la página actual y guardamos la anterior
            if choice != st.session_state.current_page:
                st.session_state.previous_page = previous_page
                st.session_state.current_page = choice

            if choice == "Mis SetLists":
                show_setlists_page()
            elif choice == "Gestionar Canciones":
                manage_songs_page()
            elif choice == "Cambiar Contraseña":
                change_password_page()
            elif choice == "Cerrar Sesión":
                st.session_state.logged_in = False
                st.session_state.user = None
                st.rerun()

def view_notes_page():
    song = st.session_state.selected_song
    st.title(f"Acordes de la canción: {song['title']}")
    
    # Incluir más detalles de la canción
    st.write(f"Tono: {song.get('key', 'No especificado')}")
    st.write(f"Tempo: {song.get('tempo', 'No especificado')}")
    
    notes = song.get('notes', 'Sin notas disponibles')
    st.text_area("Acordes", value=notes, height=800, disabled=False)
    
    if st.button("Volver"):
        st.session_state.current_page = st.session_state.previous_page
        st.session_state.selected_song = None
        st.rerun()




        
if __name__ == "__main__":
    main()
