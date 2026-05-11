# pages/5_🛠️_Settings.py
import streamlit as st
from utils import load_settings, save_settings
import pandas as pd
from pathlib import Path
import traceback

st.set_page_config(page_title="⚙️ Paramètres", layout="wide")
st.title("⚙️ Paramètres de l'application")

# -----------------------
# Chargement sûr des settings
# -----------------------
try:
    settings = load_settings()
    if not isinstance(settings, dict):
        settings = {"regions": {}, "types_borne": []}
except Exception as e:
    st.error("Impossible de charger les paramètres : " + str(e))
    st.text(traceback.format_exc())
    settings = {"regions": {}, "types_borne": []}

# -----------------------
# Containers réutilisables pour forcer le rerender
# -----------------------
_regions_table_container = st.container()
_select_region_container = st.container()
_lieux_container = st.container()
_types_container = st.container()
_message_container = st.container()

# -----------------------
# Helpers
# -----------------------
def regions_summary_df(s):
    rows = []
    for name, meta in (s.get("regions") or {}).items():
        acr = meta.get("acronyme", "") if isinstance(meta, dict) else ""
        lieux = meta.get("lieux", []) if isinstance(meta, dict) else []
        rows.append({"Région": name, "Acronyme": acr, "Nombre de lieux": len(lieux)})
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Région", "Acronyme", "Nombre de lieux"])

def safe_save_and_rerun(s, msg="Sauvegarde effectuée"):
    try:
        save_settings(s)
        _message_container.success(msg)
        # relancer la page pour recharger proprement les settings
        if hasattr(st, "experimental_rerun"):
            try:
                st.experimental_rerun()
            except Exception:
                # fallback léger : toggle session key
                st.session_state["_refresh_toggle"] = not st.session_state.get("_refresh_toggle", False)
    except Exception as e:
        _message_container.error(f"Erreur lors de la sauvegarde : {e}")
        st.text(traceback.format_exc())

# -----------------------
# Layout principal
# -----------------------
col_left, col_right = st.columns([2, 1])

with col_left:
    st.header("Régions")
    df = regions_summary_df(settings)
    with _regions_table_container:
        st.dataframe(df, use_container_width=True)

    st.markdown("### Ajouter une région")
    with st.form("form_add_region", clear_on_submit=True):
        new_region = st.text_input("Nom de la région", "")
        new_acro = st.text_input("Acronyme (optionnel)", "")
        submit_region = st.form_submit_button("Ajouter la région")
        if submit_region:
            key = new_region.strip()
            if not key:
                st.warning("Le nom de la région ne peut pas être vide.")
            else:
                if key in settings.get("regions", {}):
                    st.warning("Cette région existe déjà.")
                else:
                    settings.setdefault("regions", {})[key] = {"acronyme": new_acro.strip(), "lieux": []}
                    safe_save_and_rerun(settings, f"Région '{key}' ajoutée.")

    st.markdown("### Gérer une région existante")
    regions_list = list(settings.get("regions", {}).keys())
    if not regions_list:
        st.info("Aucune région définie pour le moment.")
    else:
        with _select_region_container:
            sel_region = st.selectbox("Sélectionner une région", [""] + regions_list, key="select_region_main")
        if sel_region:
            meta = settings["regions"].get(sel_region, {"acronyme": "", "lieux": []})
            st.subheader(f"Édition : {sel_region}")
            col_a, col_b = st.columns([2, 1])
            with col_a:
                new_name = st.text_input("Renommer la région", sel_region, key=f"rename_{sel_region}")
                new_acro = st.text_input("Acronyme", meta.get("acronyme", ""), key=f"acro_{sel_region}")
            with col_b:
                if st.button("Renommer / Mettre à jour", key=f"update_region_{sel_region}"):
                    new_name = new_name.strip()
                    if not new_name:
                        st.warning("Le nom ne peut pas être vide.")
                    else:
                        # rename if changed
                        if new_name != sel_region:
                            if new_name in settings["regions"]:
                                st.warning("Une région avec ce nom existe déjà.")
                            else:
                                settings["regions"][new_name] = settings["regions"].pop(sel_region)
                                sel_region = new_name
                        settings["regions"][sel_region]["acronyme"] = new_acro.strip()
                        safe_save_and_rerun(settings, "Région mise à jour.")

            st.markdown("#### Supprimer la région")
            if st.button("Supprimer cette région", key=f"del_region_{sel_region}"):
                confirm = st.checkbox(f"Confirmer la suppression de la région '{sel_region}'", key=f"confirm_del_{sel_region}")
                if confirm:
                    settings["regions"].pop(sel_region, None)
                    safe_save_and_rerun(settings, f"Région '{sel_region}' supprimée.")

with col_right:
    st.header("Types de borne")
    tb = settings.get("types_borne", [])
    with _types_container:
        if isinstance(tb, list) and tb:
            for t in tb:
                st.write("- ", t if isinstance(t, str) else (t.get("label") or str(t)))
        else:
            st.info("Aucun type défini")

    st.markdown("### Ajouter un type de borne")
    with st.form("form_add_type", clear_on_submit=True):
        new_type = st.text_input("Nom du type (ex: AC 22kW)", "")
        submit_type = st.form_submit_button("Ajouter le type")
        if submit_type:
            nt = new_type.strip()
            if not nt:
                st.warning("Le nom du type ne peut pas être vide.")
            else:
                settings.setdefault("types_borne", [])
                exists = any((nt == (t if isinstance(t, str) else t.get("label"))) for t in settings["types_borne"])
                if exists:
                    st.warning("Ce type existe déjà.")
                else:
                    settings["types_borne"].append(nt)
                    safe_save_and_rerun(settings, f"Type '{nt}' ajouté.")

    st.markdown("### Supprimer un type de borne")
    if settings.get("types_borne"):
        options = [(t if isinstance(t, str) else t.get("label")) for t in settings["types_borne"]]
        rem = st.multiselect("Sélectionner les types à supprimer", options=options, key="multisel_types")
        if st.button("Supprimer les types sélectionnés"):
            if rem:
                settings["types_borne"] = [t for t in settings["types_borne"] if (t if isinstance(t, str) else t.get("label")) not in rem]
                safe_save_and_rerun(settings, f"{len(rem)} type(s) supprimé(s).")
            else:
                st.warning("Aucun type sélectionné.")

# -----------------------
# Section Lieux (affichage et gestion par région)
# -----------------------
st.markdown("---")
st.header("Lieux (par région)")
regions_list = list(settings.get("regions", {}).keys())
if not regions_list:
    st.info("Aucune région définie. Créez d'abord une région.")
else:
    with _lieux_container:
        sel_region_lieux = st.selectbox("Choisir une région", [""] + regions_list, key="select_lieux_region")
        if sel_region_lieux:
            st.subheader(f"Lieux pour {sel_region_lieux}")
            lieux = settings["regions"].get(sel_region_lieux, {}).get("lieux", [])
            if lieux:
                for l in lieux:
                    st.write("- ", l)
            else:
                st.info("Aucun lieu pour cette région.")

            st.markdown("### Ajouter un lieu")
            with st.form(f"form_add_lieu_{sel_region_lieux}", clear_on_submit=True):
                new_lieu = st.text_input("Nom du lieu", "")
                submit_lieu = st.form_submit_button("Ajouter le lieu")
                if submit_lieu:
                    nl = new_lieu.strip()
                    if not nl:
                        st.warning("Le nom du lieu ne peut pas être vide.")
                    else:
                        if nl in settings["regions"][sel_region_lieux]["lieux"]:
                            st.warning("Ce lieu existe déjà pour la région.")
                        else:
                            settings["regions"][sel_region_lieux]["lieux"].append(nl)
                            safe_save_and_rerun(settings, f"Lieu '{nl}' ajouté à {sel_region_lieux}.")

            st.markdown("### Supprimer des lieux")
            lieux = settings["regions"][sel_region_lieux].get("lieux", [])
            if lieux:
                to_remove = st.multiselect("Sélectionner les lieux à supprimer", options=lieux, key=f"multisel_{sel_region_lieux}")
                if st.button("Supprimer les lieux sélectionnés"):
                    if to_remove:
                        settings["regions"][sel_region_lieux]["lieux"] = [l for l in lieux if l not in to_remove]
                        safe_save_and_rerun(settings, f"{len(to_remove)} lieu(x) supprimé(s).")
                    else:
                        st.warning("Aucun lieu sélectionné.")

# -----------------------
# Debug / état rapide
# -----------------------
st.markdown("---")
st.write("Debug rapide: nombre de régions =", len(settings.get("regions", {})), " | types =", len(settings.get("types_borne", [])))
