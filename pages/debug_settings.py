# pages/5_🛠️_Settings.py (version simplifiée et robuste)
import streamlit as st
from utils import load_settings, save_settings
import pandas as pd

st.set_page_config(page_title="Settings", layout="wide")
st.title("⚙️ Paramètres (version simplifiée)")

# Chargement sûr
try:
    settings = load_settings()
    if not isinstance(settings, dict):
        settings = {"regions": {}, "types_borne": []}
except Exception as e:
    st.error("Impossible de charger les paramètres: " + str(e))
    settings = {"regions": {}, "types_borne": []}

# Helpers d'affichage
def regions_summary(s):
    rows = []
    for name, meta in (s.get("regions") or {}).items():
        acr = meta.get("acronyme", "") if isinstance(meta, dict) else ""
        lieux = meta.get("lieux", []) if isinstance(meta, dict) else []
        rows.append({"Région": name, "Acronyme": acr, "Nombre de lieux": len(lieux)})
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Région", "Acronyme", "Nombre de lieux"])

# Layout simple: colonnes
col_left, col_right = st.columns([2, 1])

with col_left:
    st.header("Régions")
    df = regions_summary(settings)
    st.dataframe(df, use_container_width=True)

    st.markdown("### Ajouter une région")
    with st.form("add_region"):
        rname = st.text_input("Nom de la région")
        racro = st.text_input("Acronyme (optionnel)")
        if st.form_submit_button("Ajouter"):
            if not rname.strip():
                st.warning("Nom requis")
            else:
                settings.setdefault("regions", {})
                if rname in settings["regions"]:
                    st.warning("Région déjà existante")
                else:
                    settings["regions"][rname] = {"acronyme": racro.strip(), "lieux": []}
                    try:
                        save_settings(settings)
                        st.success("Région ajoutée")
                    except Exception as e:
                        st.error("Erreur sauvegarde: " + str(e))

    st.markdown("### Gérer lieux pour une région")
    regions_list = list(settings.get("regions", {}).keys())
    sel = st.selectbox("Sélectionner une région", [""] + regions_list)
    if sel:
        st.write("Lieux actuels:", settings["regions"][sel].get("lieux", []))
        with st.form(f"add_lieu_{sel}", clear_on_submit=True):
            nl = st.text_input("Nom du lieu")
            if st.form_submit_button("Ajouter lieu"):
                if nl.strip():
                    if nl in settings["regions"][sel]["lieux"]:
                        st.warning("Lieu déjà présent")
                    else:
                        settings["regions"][sel]["lieux"].append(nl.strip())
                        try:
                            save_settings(settings)
                            st.success("Lieu ajouté")
                        except Exception as e:
                            st.error("Erreur sauvegarde: " + str(e))
                else:
                    st.warning("Nom requis")

with col_right:
    st.header("Types de borne")
    tb = settings.get("types_borne", [])
    if isinstance(tb, list) and tb:
        for t in tb:
            st.write("- ", t if isinstance(t, str) else (t.get("label") or str(t)))
    else:
        st.info("Aucun type défini")

    st.markdown("### Ajouter un type")
    with st.form("add_type"):
        tlabel = st.text_input("Libellé")
        if st.form_submit_button("Ajouter"):
            if not tlabel.strip():
                st.warning("Libellé requis")
            else:
                settings.setdefault("types_borne", [])
                # normaliser en liste de strings
                if any((tlabel == (t if isinstance(t, str) else t.get("label")) ) for t in settings["types_borne"]):
                    st.warning("Type déjà présent")
                else:
                    settings["types_borne"].append(tlabel.strip())
                    try:
                        save_settings(settings)
                        st.success("Type ajouté")
                    except Exception as e:
                        st.error("Erreur sauvegarde: " + str(e))

st.markdown("---")
st.write("Debug rapide: nombre de régions =", len(settings.get("regions", {})), " | types =", len(settings.get("types_borne", [])))
