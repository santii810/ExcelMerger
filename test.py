import streamlit as st

# Inicializar el estado para rastrear la pestaña activa
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Cat"


# Función para cambiar de pestaña
def switch_tab(tab_name):
    st.session_state.active_tab = tab_name


# Simular las pestañas con condicionales
if st.session_state.active_tab == "Cat":
    st.header("A cat")
    st.image("https://static.streamlit.io/examples/cat.jpg", width=200)
    if st.button("Next: Dog"):
        switch_tab("Dog")

elif st.session_state.active_tab == "Dog":
    st.header("A dog")
    st.image("https://static.streamlit.io/examples/dog.jpg", width=200)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Previous: Cat"):
            switch_tab("Cat")
    with col2:
        if st.button("Next: Owl"):
            switch_tab("Owl")

elif st.session_state.active_tab == "Owl":
    st.header("An owl")
    st.image("https://static.streamlit.io/examples/owl.jpg", width=200)
    if st.button("Previous: Dog"):
        switch_tab("Dog")
