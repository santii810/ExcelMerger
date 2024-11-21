import pandas as pd
import re


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
