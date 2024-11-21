import pandas as pd
from io import BytesIO


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
