# DEBUG_SYNTAX — coller en tout début de pages/5_🛠️_Settings.py
import streamlit as st, ast, traceback, sys, pathlib
st.markdown("### DEBUG SYNTAX: tentative d'analyse du fichier source")
try:
    p = pathlib.Path(__file__).resolve()
    code = p.read_text(encoding="utf-8")
    try:
        ast.parse(code, filename=str(p))
        st.success("Aucune erreur de syntaxe détectée par ast.parse()")
    except SyntaxError as se:
        st.error(f"SyntaxError détectée: {se.msg}")
        st.write(f"Fichier: {se.filename}")
        st.write(f"Ligne: {se.lineno}  Colonne: {se.offset}")
        st.code(se.text or "", language="python")
        # afficher un extrait autour de la ligne fautive
        lines = code.splitlines()
        start = max(0, (se.lineno or 1) - 4)
        end = min(len(lines), (se.lineno or 1) + 2)
        excerpt = "\n".join(f"{i+1:4d}: {lines[i]}" for i in range(start, end))
        st.code(excerpt, language="python")
except Exception as e:
    st.error("Erreur inattendue lors du debug syntaxique: " + str(e))
    st.text(traceback.format_exc())
    st.stop()
# Fin DEBUG_SYNTAX

# pages/5_🛠️_Settings.py
import streamlit as st
from utils import load_settings, save_settings
import pandas as pd

st.set_page_config(page_title="Settings", layout="wide")
st.title("⚙️ Paramètres de l'application")

# -----------------------
# Chargement sûr des settings
# -----------------------
try:
    settings = load_settings()
    if not isinstance(settings, dict):
        settings = {"regions": {}, "types_borne": []}
except Exception as e:
    st.error("Impossible de charger les paramètres: " + str(e))
    settings = {"regions": {}, "types_borne": []}

# -----------------------
# Containers réutilisables pour forcer le rerender sans perdre l'état
# -----------------------
_regions_table_container = st.container()
_lieux_container = st.container()
_types_container = st.container()
_select_region_container = st.container()
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

def do_rerun():
    # appel sécurisé à experimental_rerun
    if hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()
        except Exception:
            # fallback: toggle a session_state key to force a light refresh
            st.session_state["_refresh_toggle"] = not st.session_state.get("_refresh_toggle", False)

def save_and_rerun(s, success_msg="Sauvegarde effectuée"):
    try:
        save_settings(s)
        _message_container.success(success_msg)
        do_rerun()
    except Exception as e:
        _message_container.error(f"Erreur lors de la sauvegarde : {e}")

# -----------------------
# Layout principal
# -----------------------
col_left, col_right = st.columns([2, 1])

with col_left:
    st.header("Régions")
    # Affiche le tableau des régions
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
                    save_and_rerun(settings, f"Région '{key}' ajoutée.")

    st.markdown("### Gérer une région existante")
    regions_list = list(settings.get("regions", {}).keys())
    if not regions_list:
        st.info("Aucune région définie pour le moment.")
    else:
        # selectbox dans un container pour pouvoir le recréer après save
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
                        save_and_rerun(settings, "Région mise à jour.")

            st.markdown("#### Supprimer la région")
            if st.button("Supprimer cette région", key=f"del_region_{sel_region}"):
                confirm = st.checkbox(f"Confirmer la suppression de la région '{sel_region}'", key=f"confirm_del_{sel_region}")
                if confirm:
                    settings["regions"].pop(sel_region, None)
                    save_and_rerun(settings, f"Région '{sel_region}' supprimée.")

with col_right:
    st.header("Types de borne")
    tb = settings.get("types_borne", [])
    with _types_container:
        if isinstance(tb, list) and tb:
            for t in tb:
                st.write("- ", t if isinstance(t
