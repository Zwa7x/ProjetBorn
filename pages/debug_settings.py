# pages/debug_settings.py  -- test minimal pour vérifier UI + load/save
import streamlit as st
from utils import load_settings, save_settings

st.set_page_config(page_title="DEBUG Settings", layout="wide")
st.title("DEBUG : Settings - test minimal")

# Affichage du contenu chargé
try:
    settings = load_settings()
except Exception as e:
    st.error("load_settings() a levé une exception : " + str(e))
    import traceback; st.text(traceback.format_exc())
    st.stop()

st.subheader("Résumé des settings chargés")
st.write("Type:", type(settings).__name__)
st.write("Clés racine:", list(settings.keys()))
st.write("Nombre de régions:", len(settings.get("regions", {})))
st.write("Types de borne (raw):")
st.json(settings.get("types_borne", []))

# Formulaire simple pour ajouter une région
st.markdown("---")
st.subheader("Ajouter une région (test rapide)")
with st.form("add_region_test", clear_on_submit=True):
    region_name = st.text_input("Nom de la région")
    region_acro = st.text_input("Acronyme (optionnel)")
    submitted = st.form_submit_button("Ajouter la région")
    if submitted:
        if not region_name.strip():
            st.warning("Nom requis")
        else:
            settings.setdefault("regions", {})
            if region_name in settings["regions"]:
                st.warning("Région déjà existante")
            else:
                settings["regions"][region_name] = {"acronyme": region_acro.strip(), "lieux": []}
                try:
                    save_settings(settings)
                    st.success(f"Région '{region_name}' ajoutée et sauvegardée.")
                except Exception as e:
                    st.error("Erreur save_settings(): " + str(e))

# Formulaire simple pour ajouter un type de borne
st.markdown("---")
st.subheader("Ajouter un type de borne (test rapide)")
with st.form("add_type_test", clear_on_submit=True):
    type_label = st.text_input("Libellé du type")
    submitted2 = st.form_submit_button("Ajouter le type")
    if submitted2:
        if not type_label.strip():
            st.warning("Libellé requis")
        else:
            tb = settings.setdefault("types_borne", [])
            # accepte soit liste de strings soit liste d'objets
            if isinstance(tb, list) and type_label not in [t if isinstance(t, str) else t.get("label") for t in tb]:
                tb.append(type_label)
                try:
                    save_settings(settings)
                    st.success(f"Type '{type_label}' ajouté et sauvegardé.")
                except Exception as e:
                    st.error("Erreur save_settings(): " + str(e))
            else:
                st.warning("Type déjà présent ou format inattendu.")

# Affichage final pour vérifier la persistance
st.markdown("---")
st.subheader("Etat courant après opérations")
st.write("Nombre de régions:", len(settings.get("regions", {})))
st.write("Types de borne (après):")
st.json(settings.get("types_borne", []))

st.info("Si ce test s'affiche et que l'ajout fonctionne, la page Settings d'origine contient probablement une condition qui empêche l'affichage (sélecteur, st.stop(), ou rerun).")
