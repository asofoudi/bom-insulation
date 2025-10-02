import streamlit as st
import pandas as pd
import math
from datetime import datetime

st.set_page_config(page_title="Θερμομόνωση - BOM & Προσφορά", page_icon="🧱", layout="centered")

# -----------------------------
# Helpers
# -----------------------------

def nearest_int(x: float) -> int:
    """Στρογγυλοποίηση στο πιο κοντινό ακέραιο (0.5 προς τα πάνω)."""
    return int(math.floor(x + 0.5))

# Βρίσκει συνδυασμό 10L & 3L πιο κοντά στα απαιτούμενα λίτρα (μπορεί να είναι λίγο λιγότερο ή περισσότερο)
PRIMER_PACKS = {"10 L": 10.0, "3 L": 3.0}

def nearest_primer_combo(liters_needed: float):
    if liters_needed <= 0:
        return {"10 L": 0, "3 L": 0, "total_l": 0.0, "diff_l": 0.0}
    best = None
    max_10 = max(0, nearest_int(liters_needed / PRIMER_PACKS["10 L"]) + 3)
    for n10 in range(max_10 + 1):
        for n3 in range(0, 8):
            total = n10 * PRIMER_PACKS["10 L"] + n3 * PRIMER_PACKS["3 L"]
            diff = abs(total - liters_needed)
            score = (diff, n10 + n3)  # ελάχιστη απόκλιση, μετά λιγότερα τεμάχια
            if best is None or score < best[0]:
                best = (score, n10, n3, total, diff)
    _, n10, n3, tot, diff = best
    return {"10 L": n10, "3 L": n3, "total_l": round(tot,2), "diff_l": round(diff,2)}

# -----------------------------
# Στοιχεία πελάτη / έργου
# -----------------------------
st.title("🧱 BOM Θερμομόνωσης & Πρόταση Προσφοράς")
with st.expander("Στοιχεία Πελάτη / Έργου", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Ονοματεπώνυμο / Επωνυμία", "")
        location = st.text_input("Τοποθεσία έργου", "")
    with col2:
        phone = st.text_input("Τηλέφωνο", "")
        project_label = st.text_input("Τίτλος έργου / Αναφορά", "Θερμομόνωση")

# -----------------------------
# Είσοδοι
# -----------------------------
st.header("1) Είσοδοι")
area_m2 = st.number_input("Εμβαδόν προς μόνωση (m²)", min_value=0.0, step=1.0)
ins_type = st.selectbox("Τύπος Μόνωσης", ["Εξηλασμένη", "Γραφιτούχα"], index=1)
ins_thickness = st.selectbox("Πάχος Μόνωσης", ["3 cm","4 cm","5 cm","6 cm","8 cm","10 cm","12 cm"], index=3)

st.caption("Οι υπολογισμοί γίνονται με στρογγυλοποιήσεις στο πιο κοντινό τεμάχιο/συσκευασία (και όχι πάντα προς τα πάνω).")

# -----------------------------
# Κανόνες κατανάλωσης & Συσκευασίες
# -----------------------------
COLLA_KG_PER_M2 = 8.0
COLLA_BAG_KG = 25
MESH_FACTOR = 1.10  # m²/m²
MESH_ROLL_M2 = 50
PLUGS_PER_M2 = 5.5  # 5–6 τεμ./m² μέση τιμή
PLUGS_BOX_QTY = 250
PRIMER_M2_PER_L = 11.0
PASTE_KG_PER_M2 = 2.5
PASTE_BUCKET_KG = 25

# -----------------------------
# Τιμές (χωρίς ΦΠΑ)
# -----------------------------
PRICE_INSULATION_GRAF_PER_CM_M2 = 1.0   # €/cm/m² (μόνο για γραφιτούχο φελιζόλ)
PRICE_GLUE_BAG = 8.80                   # €/σακί 25kg
PRICE_MESH_ROLL = 36.00                 # €/ρολό 50m²
PRICE_PLUGS_BOX = 35.00                 # €/κουτί 250τμχ
PRICE_PRIMER_10L = 35.00                # €/10L
PRICE_PRIMER_3L = 10.50                 # €/3L
PRICE_PASTE_BUCKET = 33.00              # €/25kg

# -----------------------------
# Υπολογισμοί
# -----------------------------
if area_m2 > 0:
    # α) Πλάκες μόνωσης
    boards_m2 = area_m2
    thickness_cm = int(ins_thickness.split()[0])
    if ins_type == "Γραφιτούχα":
        insulation_unit_price = PRICE_INSULATION_GRAF_PER_CM_M2 * thickness_cm  # €/m²
    else:
        insulation_unit_price = 0.0  # δεν δόθηκε τιμή για εξηλασμένη
    insulation_cost = boards_m2 * insulation_unit_price

    # β) Κόλλα Vitex GNK 20 easy – 8 kg/m2, σακιά 25 kg (στρογγυλοποίηση στο κοντινότερο σακί)
    glue_kg = area_m2 * COLLA_KG_PER_M2
    glue_bags_exact = glue_kg / COLLA_BAG_KG
    glue_bags = max(1, nearest_int(glue_bags_exact)) if glue_kg > 0 else 0
    glue_cost = glue_bags * PRICE_GLUE_BAG

    # γ) Υαλοπλέγμα – 1.1 m2/m2, ρολά 50 m² (κοντινότερο ρολό)
    mesh_m2 = area_m2 * MESH_FACTOR
    mesh_rolls_exact = mesh_m2 / MESH_ROLL_M2
    mesh_rolls = max(1, nearest_int(mesh_rolls_exact)) if mesh_m2 > 0 else 0
    mesh_cost = mesh_rolls * PRICE_MESH_ROLL

    # δ) Βύσματα – 5.5 τεμ./m² → κουτιά 250 τεμ. (κοντινότερο κουτί)
    plugs_qty_exact = area_m2 * PLUGS_PER_M2
    plugs_qty = max(1, nearest_int(plugs_qty_exact)) if plugs_qty_exact > 0 else 0
    plugs_boxes_exact = plugs_qty / PLUGS_BOX_QTY
    plugs_boxes = max(1, nearest_int(plugs_boxes_exact)) if plugs_qty > 0 else 0
    plugs_cost = plugs_boxes * PRICE_PLUGS_BOX

    # ε) Αστάρι – 11 m²/L → 10L & 3L (πιο κοντινός συνδυασμός συνολικών λίτρων)
    primer_liters_needed = area_m2 / PRIMER_M2_PER_L
    primer_combo = nearest_primer_combo(primer_liters_needed)
    primer_cost = primer_combo["10 L"] * PRICE_PRIMER_10L + primer_combo["3 L"] * PRICE_PRIMER_3L

    # στ) Πάστα Granikot – 2.5 kg/m² → κουβάδες 25 kg (κοντινότερος αριθμός)
    paste_kg = area_m2 * PASTE_KG_PER_M2
    paste_buckets_exact = paste_kg / PASTE_BUCKET_KG
    paste_buckets = max(1, nearest_int(paste_buckets_exact)) if paste_kg > 0 else 0
    paste_cost = paste_buckets * PRICE_PASTE_BUCKET

    # Πίνακας
    rows = [
        {"Κωδ.": "A1", "Υλικό": f"Πλάκες θερμομόνωσης ({ins_type}, {ins_thickness})", "Μονάδα": "m²", "Ποσότητα": round(boards_m2,2), "Συσκευασία": "-", "Τεμάχια": "-", "Τιμή Μονάδας": round(insulation_unit_price,2), "Σύνολο": round(insulation_cost,2)},
        {"Κωδ.": "B1", "Υλικό": "Κόλλα Vitex GNK 20 easy", "Μονάδα": "σακί", "Ποσότητα": round(glue_kg,1), "Συσκευασία": "25 kg/σακί", "Τεμάχια": glue_bags, "Τιμή Μονάδας": PRICE_GLUE_BAG, "Σύνολο": round(glue_cost,2)},
        {"Κωδ.": "C1", "Υλικό": "Υαλοπλέγμα", "Μονάδα": "ρολό", "Ποσότητα": round(mesh_m2,1), "Συσκευασία": "Ρολό 50 m²", "Τεμάχια": mesh_rolls, "Τιμή Μονάδας": PRICE_MESH_ROLL, "Σύνολο": round(mesh_cost,2)},
        {"Κωδ.": "D1", "Υλικό": "Βύσματα θερμομόνωσης", "Μονάδα": "κουτί", "Ποσότητα": plugs_qty, "Συσκευασία": "Κουτί 250 τεμ.", "Τεμάχια": plugs_boxes, "Τιμή Μονάδας": PRICE_PLUGS_BOX, "Σύνολο": round(plugs_cost,2)},
        {"Κωδ.": "E1", "Υλικό": "Αστάρι πάστας Vitex Granikot Primer", "Μονάδα": "L", "Ποσότητα": round(primer_liters_needed,2), "Συσκευασία": "10L & 3L", "Τεμάχια": f"10L: {primer_combo['10 L']}, 3L: {primer_combo['3 L']} (Σύνολο {primer_combo['total_l']} L, Διάφορα {primer_combo['diff_l']} L)", "Τιμή Μονάδας": "—", "Σύνολο": round(primer_cost,2)},
        {"Κωδ.": "F1", "Υλικό": "Πάστα Granikot", "Μονάδα": "κουβάς", "Ποσότητα": round(paste_kg,1), "Συσκευασία": "25 kg/κουβάς", "Τεμάχια": paste_buckets, "Τιμή Μονάδας": PRICE_PASTE_BUCKET, "Σύνολο": round(paste_cost,2)},
        {"Κωδ.": "G1", "Υλικό": "Γωνιόκρανα (παρελκόμενο)", "Μονάδα": "—", "Ποσότητα": "—", "Συσκευασία": "—", "Τεμάχια": "Κατά περίπτωση", "Τιμή Μονάδας": "—", "Σύνολο": "—"},
        {"Κωδ.": "G2", "Υλικό": "Αφρός χαμηλής διόγκωσης (παρελκόμενο)", "Μονάδα": "—", "Ποσότητα": "—", "Συσκευασία": "—", "Τεμάχια": "Κατά περίπτωση", "Τιμή Μονάδας": "—", "Σύνολο": "—"},
    ]

    df = pd.DataFrame(rows)

    st.header("2) Ποσότητες & Τιμές")
    st.dataframe(df, use_container_width=True)

    subtotal = round(sum([r["Σύνολο"] for r in rows if isinstance(r["Σύνολο"], (int,float))]), 2)
    st.markdown(f"**Μερικό Σύνολο (χωρίς ΦΠΑ):** {subtotal:.2f} €")

    # Πρόταση Προσφοράς
    st.header("3) Πρόταση Προσφοράς")
    st.markdown(
        f"""
        **Πελάτης:** {client_name or '-'}  
        **Τηλέφωνο:** {phone or '-'}  
        **Τοποθεσία:** {location or '-'}  
        **Έργο:** {project_label or '-'}  
        **Ημερομηνία:** {datetime.today().strftime('%d/%m/%Y')}
        """
    )

    show_prices = st.checkbox("Εμφάνιση τιμών στον εκτυπώσιμο πίνακα", value=True)
    if show_prices:
        printable = df[["Κωδ.", "Υλικό", "Μονάδα", "Τεμάχια", "Τιμή Μονάδας", "Σύνολο"]]
    else:
        printable = df[["Κωδ.", "Υλικό", "Μονάδα", "Τεμάχια"]]

    st.table(printable)

    # Λήψη CSV
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Κατέβασμα BOM + Τιμές (CSV)", data=csv, file_name="insulation_bom_priced.csv", mime="text/csv")

else:
    st.info("Δώσε m² για να γίνουν οι υπολογισμοί.")
