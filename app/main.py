import pandas as pd
import streamlit as st
import re
from io import BytesIO


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


class FileData:
    def __init__(self, file):
        self.name = file.name
        self.size = len(file.getvalue())
        self.content = None
        self.transformed_content = None
        try:
            self.content = pd.read_excel(file)  # Intentamos leer el archivo Excel
            self._process_content()  # Procesar el contenido al inicializar
        except Exception as e:
            self.error = str(e)

    def __eq__(self, other):
        if not isinstance(other, FileData):
            return False
        return self.name == other.name

    def _extract_seller(self):
        """
        Extraer el nombre del vendedor desde el nombre del archivo.
        """
        match = re.search(r"SALDOLISTE\s+([\w\-]+)", self.name)
        return match.group(1) if match else None

    def _extract_generation_date(self):
        """
        Extraer la fecha de generación desde el nombre del archivo.
        """
        match = re.search(r"(\d{4}-\d{2}-\d{2})", self.name)
        return match.group(1) if match else None

    def _process_content(self):
        """
        Procesa el contenido del archivo para eliminar totales, rellenar valores y reorganizar en formato columnar.
        También traduce las cabeceras al inglés y añade columnas de vendedor y fecha de generación.
        """
        if self.content is not None:
            df = self.content.copy()

            # Renombrar las cabeceras al inglés
            rename_map = {
                "Kunde": "CustomerID",
                "Kurzadresse": "ShortAddress",
                "Beleg": "Document",
                "Datum": "Date",
                "Soll": "Debit",
                "Saldo": "Balance",
                "Verfall < 30": "Due < 30",
                "31 - 60": "31 - 60",
                "61- 90": "61 - 90",
                "Über 90": "Over 90",
            }
            df.rename(columns=rename_map, inplace=True)

            # Paso 1: Eliminar filas de totales
            df = df[~df["ShortAddress"].str.contains(r"\*Total", na=False)]
            df = df[~df["CustomerID"].str.contains(r"Grand-Total", na=False)]

            # Paso 2: Rellenar valores faltantes en las columnas 'CustomerID' y 'ShortAddress'
            df["CustomerID"] = df["CustomerID"].fillna(method="ffill")
            df["ShortAddress"] = df["ShortAddress"].fillna(method="ffill")

            # Paso 3: Añadir columnas "Seller" y "GenerationDate"
            df["Seller"] = self._extract_seller()
            df["GenerationDate"] = self._extract_generation_date()

            # Paso 4: Reorganizar vencimientos en formato long
            melted = df.melt(
                id_vars=[
                    "CustomerID",
                    "ShortAddress",
                    "Document",
                    "Date",
                    "Debit",
                    "Balance",
                    "Seller",
                    "GenerationDate",
                ],
                value_vars=["Due < 30", "31 - 60", "61 - 90", "Over 90"],
                var_name="DueCategory",
                value_name="Amount",
            )

            # Eliminar filas donde 'Amount' sea NaN
            self.transformed_content = melted.dropna(subset=["Amount"])


class OutputGenerator:
    def __init__(self, dataframe) -> None:
        self.dataframe = dataframe

    def generate_excel(self):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            self.dataframe.to_excel(
                writer,
                index=False,
                sheet_name="Datos Combinados",
                startrow=1,
                header=False,
            )

            # Formatear la hoja
            workbook = writer.book
            worksheet = writer.sheets["Datos Combinados"]
            (max_row, max_col) = self.dataframe.shape
            column_settings = [{"header": column} for column in self.dataframe.columns]

            worksheet.add_table(
                0,
                0,
                max_row,
                max_col - 1,
                {
                    "columns": column_settings,
                    "style": "Table Style Medium 9",
                },
            )
            for i, col in enumerate(self.dataframe.columns):
                max_length = max(
                    self.dataframe[col].astype(str).map(len).max(),
                    len(col),
                )
                worksheet.set_column(i, i, max_length + 2)

        output.seek(0)
        return output


Page().start()
