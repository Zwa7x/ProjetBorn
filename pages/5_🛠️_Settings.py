import streamlit as st
from utils.settings_loader import load_settings, save_settings

st.set_page_config(page_title="⚙️ Settings", page_icon="⚙️")

# Chargement des paramètres
settings = load_settings()

# --- MENU LATERAL ---
st.sidebar.title("⚙️ Paramètres")
section = st.sidebar.radio(
    "Navigation",
    ["📍 Régions", "🏁 Lieux", "⚡ Types de bornes"]
)

st.title("⚙️ Paramètres de l'application")

# --- SECTION REGIONS ---
if section == "📍 Régions":
    st.subheader("📍 Gestion des régions")

    regions = list(settings["regions"].keys())

    st.write("Liste des régions actuelles :")
    st.dataframe({"Régions": regions})

    # Ajout d'une région
    new_region = st.text_input("Ajouter une nouvelle région")
    if st.button("➕ Ajouter la région"):
        if new_region and new_region not in settings["regions"]:
            settings["regions"][new_region] = []
            save_settings(settings)
            st.success(f"Région '{new_region}' ajoutée.")
            st.experimental_rerun()
        else:
            st.error("Cette région existe déjà ou est vide.")

# --- SECTION LIEUX ---
elif section == "🏁 Lieux":
    st.subheader("🏁 Gestion des lieux par région")

    regions = list(settings["regions"].keys())
    if not regions:
        st.warning("Aucune région disponible. Ajoutez d'abord une région.")
    else:
        region_choice = st.selectbox("Sélectionnez une région", regions)
        lieux = settings["regions"][region_choice]

        st.write(f"Lieux actuels pour **{region_choice}** :")
        st.dataframe({"Ordre": list(range(1, len(lieux)+1)), "Lieux": lieux})

        # Ajout d'un lieu
        new_lieu = st.text_input("Ajouter un nouveau lieu")
        if st.button("➕ Ajouter le lieu"):
            if new_lieu and new_lieu not in lieux:
                settings["regions"][region_choice].append(new_lieu)
                save_settings(settings)
                st.success(f"Lieu '{new_lieu}' ajouté.")
                st.experimental_rerun()
            else:
                st.error("Ce lieu existe déjà ou est vide.")

# --- SECTION TYPES DE BORNE ---
elif section == "⚡ Types de bornes":
    st.subheader("⚡ Gestion des types de bornes")

    types_borne = settings["types_borne"]
    st.write("Types de bornes actuels :")
    st.dataframe({"Types": types_borne})

    # Ajout d'un type
    new_type = st.text_input("Ajouter un type de borne")
    if st.button("➕ Ajouter le type"):
        if new_type and new_type not in types_borne:
            settings["types_borne"].append(new_type)
            save_settings(settings)
            st.success(f"Type '{new_type}' ajouté.")
            st.experimental_rerun()
        else:
            st.error("Ce type existe déjà ou est vide.")
