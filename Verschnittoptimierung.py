import streamlit as st
import pandas as pd
from io import BytesIO

# Für PDF-Erzeugung:
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


def create_pdf_from_df(df: pd.DataFrame) -> BytesIO:
    """
    Erstellt ein PDF (in Memory) aus dem DataFrame.
    Gibt den BytesIO-Buffer zurück, den man als Download anbieten kann.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    table_data = [df.columns.tolist()] + df.values.tolist()
    table = Table(table_data)

    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)

    elements = [table]
    doc.build(elements)
    buffer.seek(0)
    return buffer


def first_fit_decreasing(stock_length: float, demands: list[tuple[float, int]]):
    """
    Einfaches First-Fit-Decreasing-Verfahren für 1D-Verschnitt.
    demands = [(effektive_laenge, bedarf), ...]
    """
    # 1) Alle Zuschnitte auflisten
    items = []
    for i, (eff_length, qty) in enumerate(demands):
        for _ in range(qty):
            items.append((eff_length, i))

    # 2) Sortiere absteigend
    items.sort(key=lambda x: x[0], reverse=True)

    # 3) Liste für Stangen
    rods = []

    # 4) First-Fit: Teile einpacken
    for part_length, part_type in items:
        placed = False
        for rod in rods:
            if rod["leftover"] >= part_length:
                rod["parts"].append((part_length, part_type))
                rod["used_length"] += part_length
                rod["leftover"] = stock_length - rod["used_length"]
                placed = True
                break

        if not placed:
            rods.append({
                "rod_id": len(rods) + 1,
                "used_length": part_length,
                "leftover": stock_length - part_length,
                "parts": [(part_length, part_type)]
            })

    # 5) Ergebnis-DataFrame
    result_data = []
    for rod in rods:
        part_count = {}
        for (length, idx) in rod["parts"]:
            if (idx, length) not in part_count:
                part_count[(idx, length)] = 0
            part_count[(idx, length)] += 1

        parts_str_list = []
        for (idx, length), count in part_count.items():
            parts_str_list.append(f"{count} × {int(length)}")
        parts_str = ", ".join(parts_str_list)

        result_data.append({
            "Stange #": rod["rod_id"],
            "Verbrauchte Länge": rod["used_length"],
            "Rest": rod["leftover"],
            "Teile (Anzahl × Effektivlänge)": parts_str
        })

    df_result = pd.DataFrame(result_data)
    return df_result


def main():
    st.set_page_config(layout="wide")
    st.title("1D-Verschnittoptimierung")

    st.markdown("""
    **Heuristik**: First Fit Decreasing (vereinfacht). 
    Berücksichtigt eine konstante Schnittbreite pro Teil.
    """)

    # ---------------------------
    # 1) SIDEBAR
    # ---------------------------
    st.sidebar.header("Haupteingaben")
    stock_length = st.sidebar.number_input("Stangenlänge (mm)", value=5000, min_value=1)
    cut_width = st.sidebar.number_input("Schnittbreite (mm)", value=2, min_value=0)
    n_parts = st.sidebar.number_input("Anzahl Teil-Längen", value=2, min_value=1)

    # Button in der Sidebar
    calculate_button = st.sidebar.button("Berechnen")

    # ---------------------------
    # 2) Spalten-Layout
    # ---------------------------
    col_eingabe, col_ergebnisse = st.columns(2)

    # Linke Spalte: Eingabe der Teil-Längen/Bedarfe
    with col_eingabe:
        st.subheader("Teileingaben")
        demands = []
        for i in range(n_parts):
            c1, c2 = st.columns(2)
            with c1:
                length_i = st.number_input(f"Länge {i+1} (mm)", min_value=1, value=1000, key=f"len_{i}")
            with c2:
                qty_i = st.number_input(f"Bedarf {i+1}", min_value=1, value=10, key=f"qty_{i}")

            effective_length = length_i + cut_width
            demands.append((effective_length, qty_i))


    # Rechte Spalte: Ergebnisse
    with col_ergebnisse:
        st.subheader("Ergebnisse & PDF-Download")

        if calculate_button:
            # Berechnen
            df_result = first_fit_decreasing(stock_length, demands)

            st.dataframe(df_result, use_container_width=True)
            st.write(f"**Gesamtanzahl Stangen**: {df_result.shape[0]}")

            # PDF erstellen
            pdf_buffer = create_pdf_from_df(df_result)
            st.download_button(
                label="Ergebnisse als PDF herunterladen",
                data=pdf_buffer,
                file_name="verschnitt_result.pdf",
                mime="application/pdf"
            )
        else:
            st.info("Noch keine Berechnung durchgeführt. Bitte auf 'Berechnen' klicken.")

        st.markdown("""
        *Die "effektive" Länge berücksichtigt bereits die Schnittbreite 
        (z.B. 1480 + 2 = 1482).*
        """)



if __name__ == "__main__":
    main()
