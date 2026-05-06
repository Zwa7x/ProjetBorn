# pages/5_🛠️_Settings.py
import streamlit as st
import pandas as pd
import json
import io
from utils import load_settings, save_settings

st.set_page_config(page_title="Settings", layout="wide")
st.title("🛠️ Paramètres de l'application")

# -----------------------
# CHANGES: Chargement et normalisation des settings
# -----------------------
try:
    settings = load_settings()
    if not isinstance(settings, dict):
        raise ValueError("Format de settings invalide")
except Exception:
    st.error("Impossible de charger les paramètres. Réinitialisation aux valeurs par défaut.")
    settings = {"regions": {}, "types_borne": []}


def _normalize_settings(s):
    if not isinstance(s, dict):
        s = {"regions": {}, "types_borne": []}

    regs = s.get("regions", {})
    if not isinstance(regs, dict):
        regs = {}

    normalized = {}
    for region_name, meta in regs.items():
        if isinstance(meta, dict):
            acr = meta.get("acronyme", "") or ""
            lieux = meta.get("lieux", []) or []
            if not isinstance(lieux, list):
                if isinstance(lieux, str):
                    lieux = [l.strip() for l in lieux.split(",") if l.strip()]
                else:
                    lieux = []
            normalized[region_name] = {"acronyme": acr, "lieux": [str(x) for x in lieux]}
        else:
            if isinstance(meta, list):
                lieux = [str(x) for x in meta]
                normalized[region_name] = {"acronyme": "", "lieux": lieux}
            elif isinstance(meta, str):
                if len(meta.strip()) <= 5:
                    normalized[region_name] = {"acronyme": meta.strip(), "lieux": []}
                else:
                    normalized[region_name] = {"acronyme": "", "lieux": [meta.strip()]}
            else:
                normalized[region_name] = {"acronyme": "", "lieux": []}

    s["regions"] = normalized

    tb = s.get("types_borne", [])
    if not isinstance(tb, list):
        if isinstance(tb, str):
            s["types_borne"] = [t.strip() for t in tb.split(",") if t.strip()]
        else:
            s["types_borne"] = []
    else:
        s["types_borne"] = [str(t) for t in tb]

    return s


settings = _normalize_settings(settings)


# -----------------------
# CHANGES: Helpers locaux
# -----------------------
def persist_and_notify(settings_obj, message="Paramètres sauvegardés"):
    try:
        save_settings(settings_obj)
        st.success(message)
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")


def region_display_rows(settings_obj):
    rows = []
    regs = settings_obj.get("regions", {}) or {}
    for region, meta in regs.items():
        if not isinstance(meta, dict):
            if isinstance(meta, list):
                meta = {"acronyme": "", "lieux": [str(x) for x in meta]}
            elif isinstance(meta, str):
                meta = {"acronyme": meta if len(meta) <= 5 else "", "lieux": [] if len(meta) <= 5 else [meta]}
            else:
                meta = {"acronyme": "", "lieux": []}
        acr = meta.get("acronyme", "") or ""
        lieux = meta.get("lieux", []) or []
        if not isinstance(lieux, list):
            if isinstance(lieux, str):
                lieux = [l.strip() for l in lieux.split(",") if l.strip()]
            else:
                lieux = []
        rows.append({
            "Région": region,
            "Acronyme": acr,
            "Nombre de lieux": len(lieux),
            "Lieux (ex.)": ", ".join(lieux[:3])
        })
    if not rows:
        return pd.DataFrame(columns=["Région", "Acronyme", "Nombre de lieux", "Lieux (ex.)"])
    return pd.DataFrame(rows)


# -----------------------
# Navigation (sous-menu)
# -----------------------
st.sidebar.title("Paramètres")
section = st.sidebar.radio("Choisir la liste à modifier", ("Régions", "Lieux (par région)", "Types de borne", "Import / Export"))

# -----------------------
# Section: Régions (création / renommage / suppression)
# -----------------------
def section_regions(settings):
    st.header("Régions")
    df_regions = region_display_rows(settings)
    st.dataframe(df_regions, use_container_width=True)

    st.markdown("### Ajouter une nouvelle région")
    with st.form("form_add_region", clear_on_submit=True):
        new_region = st.text_input("Nom de la région", "")
        new_acro = st.text_input("Acronyme (optionnel)", "")
        submit_region = st.form_submit_button("Ajouter la région")
        if submit_region:
            if not new_region.strip():
                st.warning("Le nom de la région ne peut pas être vide.")
            else:
                key = new_region.strip()
                if key in settings.get("regions", {}):
                    st.warning("Cette région existe déjà.")
                else:
                    settings.setdefault("regions", {})[key] = {"acronyme": new_acro.strip(), "lieux": []}
                    persist_and_notify(settings, f"Région '{key}' ajoutée.")
                    st.experimental_rerun()

    st.markdown("### Gérer une région existante")
    regions_list = list(settings.get("regions", {}).keys())
    if not regions_list:
        st.info("Aucune région définie pour le moment.")
        return
    sel_region = st.selectbox("Sélectionner une région", [""] + regions_list)
    if not sel_region:
        return

    meta = settings["regions"].get(sel_region, {"acronyme": "", "lieux": []})
    st.subheader(f"Édition : {sel_region}")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        new_name = st.text_input("Renommer la région", sel_region)
        new_acro = st.text_input("Acronyme", meta.get("acronyme", ""))
    with col_b:
        if st.button("Renommer / Mettre à jour"):
            new_name = new_name.strip()
            if not new_name:
                st.warning("Le nom ne peut pas être vide.")
            else:
                if new_name != sel_region:
                    if new_name in settings["regions"]:
                        st.warning("Une région avec ce nom existe déjà.")
                    else:
                        settings["regions"][new_name] = settings["regions"].pop(sel_region)
                        sel_region = new_name
                settings["regions"][sel_region]["acronyme"] = new_acro.strip()
                persist_and_notify(settings, "Région mise à jour.")
                st.experimental_rerun()

    st.markdown("#### Supprimer la région")
    if st.button("Supprimer cette région", key=f"del_region_{sel_region}"):
        confirm = st.checkbox(f"Confirmer la suppression de la région '{sel_region}'")
        if confirm:
            settings["regions"].pop(sel_region, None)
            persist_and_notify(settings, f"Région '{sel_region}' supprimée.")
            st.experimental_rerun()


# -----------------------
# Section: Lieux (gestion par région)
# -----------------------
def section_lieux(settings):
    st.header("Lieux (par région)")
    regions_list = list(settings.get("regions", {}).keys())
    if not regions_list:
        st.info("Aucune région définie. Créez d'abord une région.")
        return

    sel_region = st.selectbox("Choisir une région", [""] + regions_list)
    if not sel_region:
        return

    st.subheader(f"Lieux pour {sel_region}")
    lieux = settings["regions"][sel_region].get("lieux", [])
    if lieux:
        st.write("Lieux actuels")
        for l in lieux:
            st.write(f"- {l}")
    else:
        st.info("Aucun lieu pour cette région.")

    st.markdown("### Ajouter un lieu")
    with st.form(f"form_add_lieu_{sel_region}", clear_on_submit=True):
        new_lieu = st.text_input("Nom du lieu", "")
        submit_lieu = st.form_submit_button("Ajouter le lieu")
        if submit_lieu:
            nl = new_lieu.strip()
            if not nl:
                st.warning("Le nom du lieu ne peut pas être vide.")
            else:
                if nl in settings["regions"][sel_region]["lieux"]:
                    st.warning("Ce lieu existe déjà pour la région.")
                else:
                    settings["regions"][sel_region]["lieux"].append(nl)
                    persist_and_notify(settings, f"Lieu '{nl}' ajouté à {sel_region}.")
                    st.experimental_rerun()

    st.markdown("### Supprimer des lieux")
    if lieux:
        to_remove = st.multiselect("Sélectionner les lieux à supprimer", options=lieux)
        if st.button("Supprimer les lieux sélectionnés"):
            if to_remove:
                settings["regions"][sel_region]["lieux"] = [l for l in lieux if l not in to_remove]
                persist_and_notify(settings, f"{len(to_remove)} lieu(x) supprimé(s).")
                st.experimental_rerun()
            else:
                st.warning("Aucun lieu sélectionné.")


# -----------------------
# Section: Types de borne
# -----------------------
def section_types(settings):
    st.header("Types de borne")
    types_list = settings.get("types_borne", [])
    if not types_list:
        st.info("Aucun type de borne défini.")
    else:
        st.write("Types actuels")
        for i, t in enumerate(types_list):
            st.write(f"- **{t}**")

    st.markdown("### Ajouter un type de borne")
    with st.form("form_add_type", clear_on_submit=True):
        new_type = st.text_input("Nom du type (ex: AC 22kW)", "")
        submit_type = st.form_submit_button("Ajouter le type")
        if submit_type:
            nt = new_type.strip()
            if not nt:
                st.warning("Le nom du type ne peut pas être vide.")
            else:
                if nt in settings.get("types_borne", []):
                    st.warning("Ce type existe déjà.")
                else:
                    settings.setdefault("types_borne", []).append(nt)
                    persist_and_notify(settings, f"Type '{nt}' ajouté.")
                    st.experimental_rerun()

    st.markdown("### Supprimer un type de borne")
    if settings.get("types_borne"):
        rem = st.multiselect("Sélectionner les types à supprimer", options=settings["types_borne"])
        if st.button("Supprimer les types sélectionnés"):
            if rem:
                settings["types_borne"] = [t for t in settings["types_borne"] if t not in rem]
                persist_and_notify(settings, f"{len(rem)} type(s) supprimé(s).")
                st.experimental_rerun()
            else:
                st.warning("Aucun type sélectionné.")


# -----------------------
# Section: Import / Export
# -----------------------
def section_import_export(settings):
    st.header("Import / Export rapide")
    col_imp, col_exp = st.columns(2)
    with col_imp:
        st.subheader("Importer settings depuis JSON")
        uploaded = st.file_uploader("Charger un fichier JSON", type=["json"])
        if uploaded is not None:
            try:
                loaded = json.load(uploaded)
                if not isinstance(loaded, dict):
                    st.error("Le fichier JSON doit contenir un objet racine.")
                else:
                    loaded = _normalize_settings(loaded)
                    settings = loaded
                    persist_and_notify(settings, "Paramètres importés depuis JSON.")
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"Erreur lors de l'import : {e}")

    with col_exp:
        st.subheader("Télécharger les settings actuels")
        buf = io.StringIO()
        json.dump(settings, buf, ensure_ascii=False, indent=2)
        st.download_button("Télécharger settings.json", data=buf.getvalue(), file_name="settings.json", mime="application/json")

    st.markdown("---")
    st.caption("Les modifications sont persistées dans data/settings.json via utils.save_settings().")


# -----------------------
# Dispatcher: afficher la section choisie
# -----------------------
if section == "Régions":
    section_regions(settings)
elif section == "Lieux (par région)":
    section_lieux(settings)
elif section == "Types de borne":
    section_types(settings)
elif section == "Import / Export":
    section_import_export(settings)
