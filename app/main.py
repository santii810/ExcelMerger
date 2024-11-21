from app.output_generator import OutputGenerator
import pandas as pd
import streamlit as st
from app.file_data import FileData


class Page:
    def __init__(self) -> None:
        if "uploaded_files_data" not in st.session_state:
            st.session_state.uploaded_files_data = []
        if "output_df" not in st.session_state:
            st.session_state.output_df = None

    def start(self):
        st.set_page_config(page_title="Excel merger")
        self.upload_files()
        st.divider()
        self.view_files()
        st.divider()
        self.export_files()

    def upload_files(self):
        st.header("Step 1: Upload the files")
        uploaded_files = st.file_uploader(
            "Upload or drag Excel files (xlsx, xls)",
            accept_multiple_files=True,
            type=["xlsx", "xls"],
        )

        unique_filenames = set([uploaded_file.name for uploaded_file in uploaded_files])
        if len(uploaded_files) != len(unique_filenames):
            st.markdown(
                '<h4 style="color: yellow;">Detected multiple files with same name. It will be ingnored</h4>',
                unsafe_allow_html=True,
            )
        _, rigth = st.columns([5, 1])
        with rigth:
            if st.button(
                "1. Load files",
            ):
                already_loaded = []
                st.session_state.uploaded_files_data = []
                for file in uploaded_files:
                    if file.name not in already_loaded:
                        st.session_state.uploaded_files_data.append(FileData(file))
                        already_loaded.append(file.name)

    def view_files(self):
        st.header("Step 2: Merge files")

        # Inicializar uploaded_files_data si no existe
        if "uploaded_files_data" not in st.session_state:
            st.session_state.uploaded_files_data = []

        # Mostrar archivos subidos si hay alguno
        if st.session_state.uploaded_files_data:
            for idx, file_data in enumerate(st.session_state.uploaded_files_data):
                st.subheader(f"📄 {file_data.name}")
                st.dataframe(file_data.transformed_content)
        else:
            st.info("No hay archivos subidos aún.")
        _, rigth = st.columns([5, 1])
        with rigth:
            if st.button("2. Merge data"):
                dataframes = [
                    file.transformed_content
                    for file in st.session_state.uploaded_files_data
                ]
                st.session_state.output_df = pd.concat(dataframes, ignore_index=True)

    def export_files(self):
        # with self.tab3:
        st.header("Step 3: Download data")
        if st.session_state.output_df is not None:
            generator = OutputGenerator(st.session_state.output_df)
            st.dataframe(st.session_state.output_df)
            _, rigth = st.columns([5, 1])
            with rigth:
                st.download_button(
                    label="Download",
                    data=generator.generate_excel(),
                    file_name="datos_combinados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        else:
            st.info("No hay archivos transformados para exportar.")


Page().start()
