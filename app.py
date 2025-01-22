import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import json

def init_database():
    conn = sqlite3.connect('setlist_helper.db')
    c = conn.cursor()
    
    # Crear tabla de canciones
    c.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            key TEXT,
            duration INTEGER,
            notes TEXT
        )
    ''')
    
    # Crear tabla de setlists
    c.execute('''
        CREATE TABLE IF NOT EXISTS setlists (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            date TEXT,
            songs TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_next_song_id():
    conn = sqlite3.connect('setlist_helper.db')
    c = conn.cursor()
    c.execute('SELECT MAX(id) FROM songs')
    max_id = c.fetchone()[0]
    conn.close()
    return 1 if max_id is None else max_id + 1

def add_song_to_db(title, key, duration, notes):
    conn = sqlite3.connect('setlist_helper.db')
    c = conn.cursor()
    song_id = get_next_song_id()
    c.execute('''
        INSERT INTO songs (id, title, key, duration, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (song_id, title, key, duration, notes))
    conn.commit()
    conn.close()

def get_all_songs():
    conn = sqlite3.connect('setlist_helper.db')
    c = conn.cursor()
    c.execute('SELECT * FROM songs')
    songs = c.fetchall()
    conn.close()
    return [{"id": s[0], "title": s[1], "key": s[2], "duration": s[3], "notes": s[4]} for s in songs]

def update_song(song_id, title, key, duration, notes):
    conn = sqlite3.connect('setlist_helper.db')
    c = conn.cursor()
    c.execute('''
        UPDATE songs
        SET title = ?, key = ?, duration = ?, notes = ?
        WHERE id = ?
    ''', (title, key, duration, notes, song_id))
    conn.commit()
    conn.close()

def delete_song(song_id):
    conn = sqlite3.connect('setlist_helper.db')
    c = conn.cursor()
    c.execute('DELETE FROM songs WHERE id = ?', (song_id,))
    conn.commit()
    conn.close()

def save_setlist(name, date, songs):
    conn = sqlite3.connect('setlist_helper.db')
    c = conn.cursor()
    songs_json = json.dumps(songs)
    c.execute('''
        INSERT INTO setlists (name, date, songs)
        VALUES (?, ?, ?)
    ''', (name, date, songs_json))
    conn.commit()
    conn.close()

def get_all_setlists():
    conn = sqlite3.connect('setlist_helper.db')
    c = conn.cursor()
    c.execute('SELECT * FROM setlists')
    setlists = c.fetchall()
    conn.close()
    return [{
        "id": s[0],
        "name": s[1],
        "date": s[2],
        "songs": json.loads(s[3])
    } for s in setlists]

def delete_setlist(setlist_id):
    conn = sqlite3.connect('setlist_helper.db')
    c = conn.cursor()
    c.execute('DELETE FROM setlists WHERE id = ?', (setlist_id,))
    conn.commit()
    conn.close()

def init_session_state():
    if 'current_song' not in st.session_state:
        st.session_state.current_song = None
    if 'editing_song' not in st.session_state:
        st.session_state.editing_song = None

def edit_song_form(song=None):
    with st.form("edit_song_form"):
        title = st.text_input("Título de la Canción", value=song['title'] if song else "")
        col1, col2 = st.columns(2)
        with col1:
            key = st.text_input("Tonalidad", value=song['key'] if song else "")
        with col2:
            duration = st.number_input("Duración (min)", min_value=1, value=song['duration'] if song else 3)
        notes = st.text_area("Notas", value=song['notes'] if song else "")
        
        if song:
            submitted = st.form_submit_button("Actualizar Canción")
            if submitted:
                update_song(song['id'], title, key, duration, notes)
                st.session_state.editing_song = None
                st.success("Canción actualizada!")
                st.rerun()
        else:
            submitted = st.form_submit_button("Agregar Canción")
            if submitted and title:
                add_song_to_db(title, key, duration, notes)
                st.success(f"Canción '{title}' agregada!")
                st.rerun()

def show_song_notes(song):
    st.subheader(f"Notas de: {song['title']}")
    st.write(f"**Tonalidad:** {song['key']}")
    st.write(f"**Duración:** {song['duration']} min")
    st.text_area("Notas", value=song['notes'], disabled=True, height=300)
    if st.button("Volver"):
        st.session_state.current_song = None
        st.rerun()

def show_songs_page():
    st.title("Base de Datos de Canciones")
    
    if st.session_state.current_song:
        show_song_notes(st.session_state.current_song)
        return
    
    if st.session_state.editing_song:
        st.subheader("Editar Canción")
        edit_song_form(st.session_state.editing_song)
    else:
        edit_song_form()
    
    songs = get_all_songs()
    if songs:
        st.subheader("Canciones Guardadas")
        for song in songs:
            col1, col2, col3, col4 = st.columns([3,1,1,1])
            with col1:
                st.write(f"{song['id']}. {song['title']} ({song['key']})")
            with col2:
                if st.button("Ver Notas", key=f"song_{song['id']}"):
                    st.session_state.current_song = song
                    st.rerun()
            with col3:
                if st.button("Editar", key=f"edit_{song['id']}"):
                    st.session_state.editing_song = song
                    st.rerun()
            with col4:
                if st.button("Eliminar", key=f"del_{song['id']}"):
                    delete_song(song['id'])
                    st.success(f"Canción eliminada!")
                    st.rerun()

def show_setlist_page():
    st.title("Crear SetList")
    
    if st.session_state.current_song:
        show_song_notes(st.session_state.current_song)
        return

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
            st.rerun()
    
    setlists = get_all_setlists()
    if setlists:
        st.subheader("SetLists Guardados")
        for setlist in setlists:
            col1, col2 = st.columns([4,1])
            with col1:
                with st.expander(f"{setlist['name']} - {setlist['date']}"):
                    for song in setlist['songs']:
                        col1, col2 = st.columns([4,1])
                        with col1:
                            st.write(f"{song['title']} ({song['key']})")
                        with col2:
                            if st.button("Ver Notas", key=f"setlist_{setlist['id']}_song_{song['id']}"):
                                st.session_state.current_song = song
                                st.rerun()
            with col2:
                if st.button("Eliminar SetList", key=f"del_setlist_{setlist['id']}"):
                    delete_setlist(setlist['id'])
                    st.success("SetList eliminado!")
                    st.rerun()

def main():
    init_database()
    init_session_state()
    
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a:", ["Canciones", "SetLists"])
    
    if page == "Canciones":
        show_songs_page()
    else:
        show_setlist_page()

if __name__ == "__main__":
    main()
