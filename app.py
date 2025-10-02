import streamlit as st
import pandas as pd
import math
from datetime import datetime

def ceil(x):
    return int(math.ceil(x))

st.set_page_config(page_title="Θερμομόνωση - BOM & Προσφορά", page_icon="🧱", layout="centered")

st.title("🧱 BOM Θερμομόνωσης & Πρόταση Προσφοράς")

# --- Στοιχεία πελάτη / έργου ---
with st.expander("Στοιχεία Πελάτη / Έργου", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Ονοματεπώνυμο / Επωνυμία", "")
        location = st.text_input("Τοποθεσία έργου", "")
    with col2:
        phone = st.text_input("Τηλέφωνο", "")
        project_label = st.text_input("Τίτλος έργου / Αναφορά", "Θερμομόνωση")

# --- Είσοδοι υπολογισμών ---
st.header("1) Είσοδοι")
area_m2 = st.number_input("Εμβαδόν προς μόνωση (m²)", min_value=0.0, step=1.0)
ins_type = st.selectbox("Τύπος Μόνωσης", ["Εξηλασμένη", "Γραφιτούχα"], index=0)
ins_thickness = st.selectbox("Πάχος Μόνωσης", ["3 cm","4 cm","5 cm","6 cm","8 cm","10 cm","12 cm"], index=3)

st.caption("Οι υπολογισμοί γίνονται για τυπικές καταναλώσεις και στρογγυλοποιήσεις σε συσκευασίες.")

# --- Κανόνες κατανάλωσης & συσκευασίες ---
COLLA_KG_PER_M2 = 8.0
COLLA_BAG_KG = 25
MESH_FACTOR = 1.10  # m²/m²
MESH_ROLL_M2 = 50
PLUGS_PER_M2 = 5.5  # 5–6 τεμ./m² μέση τιμή
PLUGS_BOX_QTY = 250
PRIMER_M2_PER_L = 11.0
PRIMER_PACKS = {"10 L": 10.0, "3 L": 3.0}
PASTE_KG_PER_M2 = 2.5
PASTE_BUCKET_KG = 25

# --- Υπολογισμοί ---
def compute_primer_packs(liters_needed: float):
    # Βρίσκει συνδυασμό 10L & 3L που να καλύπτει την απαίτηση με ελάχιστη υπέρβαση
    best = None
    max_10 = ceil(liters_needed / PRIMER_PACKS["10 L"]) + 2
    for n10 in range(max_10 + 1):
        for n3 in range(0, 6):
            total_l = n10 * PRIMER_PACKS["10 L"] + n3 * PRIMER_PACKS["3 L"]
            if total_l >= liters_needed:
                over = total_l - liters_needed
                score = (over, n10 + n3)  # ελαχιστοποίηση υπέρβασης, μετά τεμαχίων
                if best is None or score < best[0]:
                    best = (score, n10, n3, total_l)
                break
    if best is None:
        return {"10 L": 0, "3 L": 0, "total_l": 0.0, "over_l": 0.0}
    (_, n10, n3, tot) = best
    return {"10 L": n10, "3 L": n3, "total_l": round(tot,2), "over_l": round(tot - liters_needed,2)}

if area_m2 > 0:
    # α) Πλάκες μόνωσης
    boards_m2 = area_m2

    # β) Κόλλα Vitex GNK 20 easy – 8 kg/m2, σακιά 25 kg
    glue_kg = area_m2 * COLLA_KG_PER_M2
    glue_bags = ceil(glue_kg / COLLA_BAG_KG)

    # γ) Υαλοπλέγμα – 1.1 m2/m2, ρολά 50 m²
    mesh_m2 = area_m2 * MESH_FACTOR
    mesh_rolls = ceil(mesh_m2 / MESH_ROLL_M2)

    # δ) Βύσματα – 5.5 τεμ./m², κουτιά 250 τεμ.
    plugs_qty = ceil(area_m2 * PLUGS_PER_M2)
    plugs_boxes = ceil(plugs_qty / PLUGS_BOX_QTY)

    # ε) Αστάρι πάστας – 11 m²/L, συσκ. 10L & 3L
    primer_liters = area_m2 / PRIMER_M2_PER_L
    primer_combo = compute_primer_packs(primer_liters)

    # στ) Πάστα Granikot – 2.5 kg/m², κουβάδες 25 kg
    paste_kg = area_m2 * PASTE_KG_PER_M2
    paste_buckets = ceil(paste_kg / PASTE_BUCKET_KG)

    # Συγκεντρωτικός πίνακας
    data = [
        {"Κωδ.": "A1", "Υλικό": f"Πλάκες θερμομόνωσης ({ins_type}, {ins_thickness})", "Μονάδα": "m²", "Ποσότητα": round(boards_m2,2), "Συσκευασία": "-", "Τεμάχια": "-"},
        {"Κωδ.": "B1", "Υλικό": "Κόλλα Vitex GNK 20 easy", "Μονάδα": "kg", "Ποσότητα": round(glue_kg,1), "Συσκευασία": "25 kg/σακί", "Τεμάχια": glue_bags},
        {"Κωδ.": "C1", "Υλικό": "Υαλοπλέγμα", "Μονάδα": "m²", "Ποσότητα": round(mesh_m2,1), "Συσκευασία": "Ρολό 50 m²", "Τεμάχια": mesh_rolls},
        {"Κωδ.": "D1", "Υλικό": "Βύσματα θερμομόνωσης", "Μονάδα": "τεμ.", "Ποσότητα": plugs_qty, "Συσκευασία": "Κουτί 250 τεμ.", "Τεμάχια": plugs_boxes},
        {"Κωδ.": "E1", "Υλικό": "Αστάρι πάστας Vitex Granikot Primer", "Μονάδα": "L", "Ποσότητα": round(primer_liters,2), "Συσκευασία": "10L & 3L", "Τεμάχια": f"10L: {primer_combo['10 L']}, 3L: {primer_combo['3 L']} (Σύνολο {primer_combo['total_l']} L)"},
        {"Κωδ.": "F1", "Υλικό": "Πάστα Granikot", "Μονάδα": "kg", "Ποσότητα": round(paste_kg,1), "Συσκευασία": "Κουβάς 25 kg", "Τεμάχια": paste_buckets},
        {"Κωδ.": "G1", "Υλικό": "Γωνιόκρανα (παρελκόμενο)", "Μονάδα": "-", "Ποσότητα": "-", "Συσκευασία": "-", "Τεμάχια": "Κατά περίπτωση"},
        {"Κωδ.": "G2", "Υλικό": "Αφρός χαμηλής διόγκωσης (παρελκόμενο)", "Μονάδα": "-", "Ποσότητα": "-", "Συσκευασία": "-", "Τεμάχια": "Κατά περίπτωση"},
    ]

    df = pd.DataFrame(data)

    st.header("2) Ποσότητες Υλικών")
    st.dataframe(df, use_container_width=True)

    st.markdown(
        f"""
        **Σημειώσεις στρογγυλοποίησης**
        - Κόλλα: {COLLA_KG_PER_M2} kg/m² → σακιά {COLLA_BAG_KG} kg (πάντα προς τα πάνω)
        - Υαλοπλέγμα: {MESH_FACTOR} m²/m² → ρολά {MESH_ROLL_M2} m²
        - Βύσματα: {PLUGS_PER_M2} τεμ./m² → κουτιά {PLUGS_BOX_QTY} τεμ.
        - Αστάρι: {PRIMER_M2_PER_L} m²/L → συσκ. 10L & 3L (ελάχιστη υπέρβαση)
        - Πάστα: {PASTE_KG_PER_M2} kg/m² → κουβάς {PASTE_BUCKET_KG} kg
        """
    )

    # --- Πρόταση Προσφοράς (εκτυπώσιμο) ---
    st.header("3) Πρόταση Προσφοράς (χωρίς τιμές)")
    st.markdown(
        f"""
        **Πελάτης:** {client_name or '-'}  
        **Τηλέφωνο:** {phone or '-'}  
        **Τοποθεσία:** {location or '-'}  
        **Έργο:** {project_label or '-'}  
        **Ημερομηνία:** {datetime.today().strftime('%d/%m/%Y')}
        """
    )
    st.table(df[["Κωδ.", "Υλικό", "Μονάδα", "Ποσότητα", "Συσκευασία", "Τεμάχια"]])

    # Λήψη CSV για αποστολή/αρχειοθέτηση
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Κατέβασμα BOM (CSV)", data=csv, file_name="insulation_bom.csv", mime="text/csv")

else:
    st.info("Δώσε m² για να γίνουν οι υπολογισμοί.")
