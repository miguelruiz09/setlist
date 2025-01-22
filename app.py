import streamlit as st
import pandas as pd
from datetime import datetime

def init_session_state():
    if 'songs_db' not in st.session_state:
        st.session_state.songs_db = []
    if 'setlists' not in st.session_state:
        st.session_state.setlists = []
    if 'page' not in st.session_state:
        st.session_state.page = 'main'
    if 'song_counter' not in st.session_state:
        st.session_state.song_counter = 1
    if 'current_song' not in st.session_state:
        st.session_state.current_song = None
    if 'editing_song' not in st.session_state:
        st.session_state.editing_song = None

def add_song_to_db(title, key, duration, notes):
    new_song = {
        "id": st.session_state.song_counter,
        "title": title,
        "key": key,
        "duration": duration,
        "notes": notes
    }
    st.session_state.songs_db.append(new_song)
    st.session_state.song_counter += 1

def update_song(song_id, title, key, duration, notes):
    for song in st.session_state.songs_db:
        if song['id'] == song_id:
            song.update({
                "title": title,
                "key": key,
                "duration": duration,
                "notes": notes
            })

def delete_song(song_id):
    st.session_state.songs_db = [song for song in st.session_state.songs_db if song['id'] != song_id]
    # Actualizar setlists que contengan esta canción
    for setlist in st.session_state.setlists:
        setlist['songs'] = [song for song in setlist['songs'] if song['id'] != song_id]

def delete_setlist(index):
    st.session_state.setlists.pop(index)

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
    
    if st.session_state.songs_db:
        st.subheader("Canciones Guardadas")
        for song in st.session_state.songs_db:
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

    with st.form("setlist_form"):
        setlist_name = st.text_input("Nombre del SetList")
        setlist_date = st.date_input("Fecha del SetList", datetime.now())
        
        available_songs = {f"{song['id']}. {song['title']} ({song['key']})": song 
                         for song in st.session_state.songs_db}
        
        selected_songs = st.multiselect(
            "Selecciona y ordena las canciones",
            options=list(available_songs.keys())
        )
        
        submitted = st.form_submit_button("Crear SetList")
        
        if submitted and setlist_name and selected_songs:
            new_setlist = {
                "name": setlist_name,
                "date": setlist_date.strftime("%Y-%m-%d"),
                "songs": [available_songs[song] for song in selected_songs]
            }
            st.session_state.setlists.append(new_setlist)
            st.success("SetList creado!")
    
    if st.session_state.setlists:
        st.subheader("SetLists Guardados")
        for i, setlist in enumerate(st.session_state.setlists):
            col1, col2 = st.columns([4,1])
            with col1:
                with st.expander(f"{i+1}. {setlist['name']} - {setlist['date']}"):
                    for song in setlist['songs']:
                        col1, col2 = st.columns([4,1])
                        with col1:
                            st.write(f"{song['title']} ({song['key']})")
                        with col2:
                            if st.button("Ver Notas", key=f"setlist_{i}_song_{song['id']}"):
                                st.session_state.current_song = song
                                st.rerun()
            with col2:
                if st.button("Eliminar SetList", key=f"del_setlist_{i}"):
                    delete_setlist(i)
                    st.success("SetList eliminado!")
                    st.rerun()

def show_song_notes(song):
    st.subheader(f"Notas de: {song['title']}")
    st.write(f"**Tonalidad:** {song['key']}")
    st.write(f"**Duración:** {song['duration']} min")
    st.text_area("Notas", value=song['notes'], disabled=True, height=300)
    if st.button("Volver"):
        st.session_state.current_song = None
        st.rerun()

def main():
    init_session_state()
    
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a:", ["Canciones", "SetLists"])
    
    if page == "Canciones":
        show_songs_page()
    else:
        show_setlist_page()

if __name__ == "__main__":
    main()