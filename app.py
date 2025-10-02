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
# ERP Codes (ανά είδος/πάχος)
# -----------------------------
ERP = {
    "GLUE": "896-0201774",  # Κόλλα Vitex GNK 20 easy
    "MESH": "899-ΥΑΛ-160",   # Υαλόπλεγμα (ποσότητα σε m²)
    "PLUGS": {  # Βύσματα ανά πάχος
        10: "99-ΒΘ-10-160/1",
        7:  "99-ΒΘ-10-140/1",
        5:  "99-ΒΘ-10-120/1",
    },
    "EPS_GRAF": {  # Γραφιτούχο φελιζόλ (πλάκες) ανά πάχος
        5: "897-06-05.01",
        7: "897-06-07 3",
        10: "897-06-10 3",
    },
    "PRIMER_10L": "899-2000732",
    "PRIMER_3L":  "899-2000731",
    "PASTE":      "896-2000735",
}

# -----------------------------
# UI - Στοιχεία πελάτη / έργου
# -----------------------------
st.title("🧱 BOM Θερμομόνωσης & Πρόταση Προσφοράς (τιμές με ΦΠΑ)")
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
ins_thickness = st.selectbox("Πάχος Μόνωσης", ["5 cm","7 cm","10 cm"], index=0)

st.caption("Οι τιμές περιλαμβάνουν ΦΠΑ. Οι στρογγυλοποιήσεις γίνονται στο πιο κοντινό τεμάχιο/συσκευασία.")

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
# Τιμές (με ΦΠΑ)
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
    thickness_cm = int(ins_thickness.split()[0])

    # α) Πλάκες μόνωσης (Γραφιτούχα: τιμή ανά cm/m²)
    boards_m2 = area_m2
    if ins_type == "Γραφιτούχα":
        insulation_unit_price = PRICE_INSULATION_GRAF_PER_CM_M2 * thickness_cm  # €/m²
        insulation_code = ERP["EPS_GRAF"].get(thickness_cm, "—")
    else:
        insulation_unit_price = 0.0  # δεν δόθηκε τιμή για εξηλασμένη
        insulation_code = "—"
    insulation_cost = boards_m2 * insulation_unit_price

    # β) Κόλλα Vitex GNK 20 easy – 8 kg/m2, σακιά 25 kg (κοντινότερο σακί)
    glue_kg = area_m2 * COLLA_KG_PER_M2
    glue_bags_exact = glue_kg / COLLA_BAG_KG
    glue_bags = max(1, nearest_int(glue_bags_exact)) if glue_kg > 0 else 0
    glue_cost = glue_bags * PRICE_GLUE_BAG

    # γ) Υαλοπλέγμα – 1.1 m2/m2, ρολά 50 m² (κοντινότερο ρολό) | ζητήθηκε ποσότητα σε m²
    mesh_m2 = area_m2 * MESH_FACTOR
    mesh_rolls_exact = mesh_m2 / MESH_ROLL_M2
    mesh_rolls = max(1, nearest_int(mesh_rolls_exact)) if mesh_m2 > 0 else 0
    mesh_cost = mesh_rolls * PRICE_MESH_ROLL

    # δ) Βύσματα – 5.5 τεμ./m² → κουτιά 250 τεμ. (κοντινότερο κουτί) | ERP ανά πάχος
    plugs_qty_exact = area_m2 * PLUGS_PER_M2
    plugs_qty = max(1, nearest_int(plugs_qty_exact)) if plugs_qty_exact > 0 else 0
    plugs_boxes_exact = plugs_qty / PLUGS_BOX_QTY
    plugs_boxes = max(1, nearest_int(plugs_boxes_exact)) if plugs_qty > 0 else 0
    plugs_cost = plugs_boxes * PRICE_PLUGS_BOX
    plugs_code = ERP["PLUGS"].get(thickness_cm, "—")

    # ε) Αστάρι – 11 m²/L → 10L & 3L (πιο κοντινός συνδυασμός) | 2 γραμμές (10L & 3L)
    primer_liters_needed = area_m2 / PRIMER_M2_PER_L
    primer_combo = nearest_primer_combo(primer_liters_needed)
    primer10_qty = primer_combo["10 L"]
    primer3_qty = primer_combo["3 L"]
    primer10_cost = primer10_qty * PRICE_PRIMER_10L
    primer3_cost = primer3_qty * PRICE_PRIMER_3L

    # στ) Πάστα Granikot – 2.5 kg/m² → κουβάδες 25 kg (κοντινότερος αριθμός)
    paste_kg = area_m2 * PASTE_KG_PER_M2
    paste_buckets_exact = paste_kg / PASTE_BUCKET_KG
    paste_buckets = max(1, nearest_int(paste_buckets_exact)) if paste_kg > 0 else 0
    paste_cost = paste_buckets * PRICE_PASTE_BUCKET

    # Πίνακας με ERP codes για copy-paste
    rows = [
        {"Κωδ.": insulation_code, "Υλικό": f"Πλάκες θερμομόνωσης ({ins_type}, {ins_thickness})", "Μονάδα": "m²", "Ποσότητα": round(boards_m2,2), "Συσκευασία": "-", "Τεμάχια": "-", "Τιμή Μονάδας": round(insulation_unit_price,2), "Σύνολο": round(insulation_cost,2)},
        {"Κωδ.": ERP["GLUE"], "Υλικό": "Κόλλα Vitex GNK 20 easy", "Μονάδα": "σακί", "Ποσότητα": round(glue_kg,1), "Συσκευασία": "25 kg/σακί", "Τεμάχια": glue_bags, "Τιμή Μονάδας": PRICE_GLUE_BAG, "Σύνολο": round(glue_cost,2)},
        {"Κωδ.": ERP["MESH"], "Υλικό": "Υαλοπλέγμα (ποσότητα σε m²)", "Μονάδα": "m²", "Ποσότητα": round(mesh_m2,1), "Συσκευασία": "Ρολό 50 m²", "Τεμάχια": mesh_rolls, "Τιμή Μονάδας": PRICE_MESH_ROLL, "Σύνολο": round(mesh_cost,2)},
        {"Κωδ.": plugs_code, "Υλικό": "Βύσματα θερμομόνωσης", "Μονάδα": "κουτί", "Ποσότητα": plugs_qty, "Συσκευασία": "Κουτί 250 τεμ.", "Τεμάχια": plugs_boxes, "Τιμή Μονάδας": PRICE_PLUGS_BOX, "Σύνολο": round(plugs_cost,2)},
        {"Κωδ.": ERP["PRIMER_10L"], "Υλικό": "Αστάρι Vitex Granikot Primer 10L", "Μονάδα": "τεμ.", "Ποσότητα": primer10_qty, "Συσκευασία": "10 L", "Τεμάχια": primer10_qty, "Τιμή Μονάδας": PRICE_PRIMER_10L, "Σύνολο": round(primer10_cost,2)},
        {"Κωδ.": ERP["PRIMER_3L"], "Υλικό": "Αστάρι Vitex Granikot Primer 3L", "Μονάδα": "τεμ.", "Ποσότητα": primer3_qty, "Συσκευασία": "3 L", "Τεμάχια": primer3_qty, "Τιμή Μονάδας": PRICE_PRIMER_3L, "Σύνολο": round(primer3_cost,2)},
        {"Κωδ.": ERP["PASTE"], "Υλικό": "Πάστα Granikot", "Μονάδα": "κουβάς", "Ποσότητα": paste_buckets, "Συσκευασία": "25 kg/κουβάς", "Τεμάχια": paste_buckets, "Τιμή Μονάδας": PRICE_PASTE_BUCKET, "Σύνολο": round(paste_cost,2)},
    ]

    df = pd.DataFrame(rows)

    st.header("2) Ποσότητες & Τιμές (με ΦΠΑ)")
    st.dataframe(df, use_container_width=True)

    subtotal = round(sum([r["Σύνολο"] for r in rows if isinstance(r["Σύνολο"], (int,float))]), 2)
    st.markdown(f"**Σύνολο (με ΦΠΑ):** {subtotal:.2f} €")

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

    printable = df[["Κωδ.", "Υλικό", "Μονάδα", "Τεμάχια", "Τιμή Μονάδας", "Σύνολο"]]
    st.table(printable)

    # Λήψη CSV
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Κατέβασμα BOM + Τιμές (CSV)", data=csv, file_name="insulation_bom_priced.csv", mime="text/csv")

else:
    st.info("Δώσε m² για να γίνουν οι υπολογισμοί.")
