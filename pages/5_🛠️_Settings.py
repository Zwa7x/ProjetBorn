# pages/5_🛠️_Settings.py
import streamlit as st
import pandas as pd
import json
import io
import re
from utils import load_settings, save_settings

st.set_page_config(page_title="Settings", layout="wide")
st.title("🛠️ Paramètres de l'application")

# -----------------------
# Chargement et normalisation des settings
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
# Containers pour affichages dynamiques
# -----------------------
_regions_table_container = st.empty()
_lieux_list_container = st.empty()
_types_list_container = st.empty()
_message_container = st.empty()

# -----------------------
# Helpers locaux (sauvegarde sûre + rerun via session_state)
# -----------------------
def persist_and_notify(settings_obj, message="Paramètres sauvegardés"):
    try:
        save_settings(settings_obj)
        _message_container.success(message)
        st.session_state["_need_rerun"] = True
    except Exception as e:
        _message_container.error(f"Erreur lors de la sauvegarde : {e}")


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


def render_regions_table():
    df_regions = region_display_rows(settings)
    _regions_table_container.dataframe(df_regions, use_container_width=True)


def render_types_list():
    _types_list_container.empty()
    types_list = settings.get("types_borne", [])
    if types_list:
        with _types_list_container.container():
            st.write("Types actuels")
            for t in types_list:
                st.write(f"- **{t}**")
    else:
        _types_list_container.info("Aucun type de borne défini.")


def render_lieux_list(sel_region):
    _lieux_list_container.empty()
    if not sel_region:
        return
    lieux = settings["regions"].get(sel_region, {}).get("lieux", [])
    if lieux:
        with _lieux_list_container.container():
            st.write("Lieux actuels")
            for l in lieux:
                st.write(f"- {l}")
    else:
        _lieux_list_container.info("Aucun lieu pour cette région.")


# -----------------------
# Import Excel helpers (flexible detection)
# -----------------------
def _merge_region_into_settings(settings_obj, region_name, acronyme, lieux_list):
    regs = settings_obj.setdefault("regions", {})
    if region_name in regs:
        if acronyme:
            regs[region_name]["acronyme"] = acronyme
        existing = regs[region_name].get("lieux", []) or []
        merged = existing[:]
        for l in lieux_list:
            if l not in merged:
                merged.append(l)
        regs[region_name]["lieux"] = merged
    else:
        regs[region_name] = {"acronyme": acronyme or "", "lieux": list(dict.fromkeys(lieux_list))}


def _find_sheet_with_column(xls_dict, candidate_column_names):
    """
    xls_dict : dict of DataFrames (sheet_name -> df)
    candidate_column_names : iterable of candidate column names (lowercase)
    Returns: (sheet_name, df) or (None, None)
    """
    # priority: exact sheet names 'Regions' or 'Types'
    for target in ("regions", "types"):
        for n in xls_dict.keys():
            if n.lower().strip() == target:
                return n, xls_dict[n].fillna("")

    # otherwise scan sheets for a matching column
    for name, df in xls_dict.items():
        cols = [str(c).strip().lower() for c in df.columns]
        if any(cand in cols for cand in candidate_column_names):
            return name, df.fillna("")
    return None, None


def import_preview_from_excel(uploaded_file):
    """
    Read uploaded Excel and return a minimal preview:
    - sheets list
    - preview DataFrame for detected Regions sheet (or None)
    - preview DataFrame for detected Types sheet (or None)
    - indication if the Region column is treated as acronym (threshold 80%)
    """
    try:
        xls = pd.read_excel(uploaded_file, sheet_name=None, engine="openpyxl")
    except Exception as e:
        raise ValueError(f"Impossible de lire le fichier Excel : {e}")

    preview = {
        "sheets": list(xls.keys()),
        "regions_df": None,
        "types_df": None,
        "regions_sheet": None,
        "types_sheet": None,
        "regions_are_acro": False,
        "detected_region_col": None,
        "detected_fullname_col": None
    }

    # detect Regions sheet (by name or by column)
    region_candidates = ("region", "région", "region_name", "regionname", "nom_region", "libelle", "region_full")
    sheet_r, df_r = _find_sheet_with_column(xls, region_candidates)
    if sheet_r:
        df_r = df_r.fillna("")
        preview["regions_sheet"] = sheet_r
        preview["regions_df"] = df_r.head(10)
        cols = [str(c).strip() for c in df_r.columns]

        # detect explicit short column (acronyme) or region column
        short_col_candidates = ("acronyme", "acro", "acronym", "code_region", "region_code")
        short_col = next((c for c in cols if c.strip().lower() in short_col_candidates), None)
        region_col = next((c for c in cols if c.strip().lower() in region_candidates), None)
        fullname_candidates = ("region_name", "nom_region", "libelle", "region_full", "region_long")
        fullname_col = next((c for c in cols if c.strip().lower() in fullname_candidates and c != region_col), None)

        # heuristic threshold now 80%
        threshold = 0.8

        if short_col:
            preview["regions_are_acro"] = True
            preview["detected_region_col"] = short_col
            preview["detected_fullname_col"] = fullname_col or region_col
        elif region_col:
            vals = [str(v).strip() for v in df_r[region_col].tolist() if str(v).strip()]
            if vals:
                short_ratio = sum(1 for v in vals if len(v) <= 5) / len(vals)
                preview["regions_are_acro"] = (short_ratio >= threshold)
            else:
                preview["regions_are_acro"] = False
            preview["detected_region_col"] = region_col
            preview["detected_fullname_col"] = fullname_col

    # detect Types sheet
    type_candidates = ("type", "type_borne", "type_bornes", "type_de_borne", "type(s)")
    sheet_t, df_t = _find_sheet_with_column(xls, type_candidates)
    if sheet_t:
        preview["types_sheet"] = sheet_t
        preview["types_df"] = df_t.head(10)

    return preview


# -----------------------
# Upsert helpers and import with upsert behavior
# -----------------------
def _upsert_region(settings_obj, region_key, acronyme, lieux_list):
    """
    Upsert helper:
    - region_key : clé utilisée dans settings (ici on can use acronyme as key if requested)
    - acronyme : value to store in 'acronyme'
    - lieux_list : list of lieux to merge
    Returns: dict {created:bool, acr_updated:bool, new_lieux:int}
    """
    regs = settings_obj.setdefault("regions", {})
    created = False
    acr_updated = False
    new_lieux_count = 0

    if region_key in regs:
        meta = regs[region_key] or {"acronyme": "", "lieux": []}
        # update acronyme if provided and different
        if acronyme and str(meta.get("acronyme", "")).strip() != acronyme:
            meta["acronyme"] = acronyme
            acr_updated = True
        # merge lieux without duplicates
        existing = meta.get("lieux", []) or []
        for l in lieux_list:
            if l and l not in existing:
                existing.append(l)
                new_lieux_count += 1
        meta["lieux"] = existing
        regs[region_key] = meta
    else:
        # create new region
        regs[region_key] = {"acronyme": acronyme or "", "lieux": list(dict.fromkeys([l for l in lieux_list if l]))}
        created = True
        new_lieux_count = len(regs[region_key]["lieux"])

    return {"created": created, "acr_updated": acr_updated, "new_lieux": new_lieux_count}


def apply_import_from_excel_upsert(uploaded_file, settings_obj):
    """
    Lecture Excel + upsert intelligent :
    - n'ajoute que les régions/types/lieux manquants
    - met à jour l'acronyme si différent
    - utilise le seuil 0.8 pour détecter colonne d'acronymes
    Returns summary dict.
    """
    try:
        xls = pd.read_excel(uploaded_file, sheet_name=None, engine="openpyxl")
    except Exception as e:
        raise ValueError(f"Impossible de lire le fichier Excel : {e}")

    added_regions = 0
    updated_regions = 0
    added_lieux = 0
    updated_acronymes = 0
    added_types = 0

    # --- Regions (flexible detection) ---
    region_candidates = ("region", "région", "region_name", "regionname", "nom_region", "libelle", "region_full")
    sheet_r, df_r = _find_sheet_with_column(xls, region_candidates)
    if sheet_r and df_r is not None:
        df_r = df_r.fillna("")
        cols = [str(c).strip() for c in df_r.columns]

        short_col_candidates = ("acronyme", "acro", "acronym", "code_region", "region_code")
        fullname_candidates = ("region_name", "nom_region", "libelle", "region_full", "region_long")

        short_col = next((c for c in cols if c.strip().lower() in short_col_candidates), None)
        region_col = next((c for c in cols if c.strip().lower() in region_candidates), None)
        fullname_col = next((c for c in cols if c.strip().lower() in fullname_candidates and c != region_col), None)

        threshold = 0.8

        # decide if short column is acronym
        if short_col:
            treat_region_as_acro = True
            detected_short_col = short_col
            detected_fullname_col = fullname_col or region_col
        elif region_col:
            vals = [str(v).strip() for v in df_r[region_col].tolist() if str(v).strip()]
            if vals:
                short_ratio = sum(1 for v in vals if len(v) <= 5) / len(vals)
                treat_region_as_acro = (short_ratio >= threshold)
            else:
                treat_region_as_acro = False
            detected_short_col = region_col
            detected_fullname_col = fullname_col
        else:
            treat_region_as_acro = False
            detected_short_col = None
            detected_fullname_col = None

        # iterate rows and upsert
        for _, row in df_r.iterrows():
            if treat_region_as_acro:
                acr = str(row.get(detected_short_col, "")).strip() if detected_short_col else ""
                fullname = str(row.get(detected_fullname_col, "")).strip() if detected_fullname_col else ""
                # use acronym as key (requested)
                region_key = acr or fullname or ""
                region_acro = acr or ""
                if not region_key:
                    continue
                lieux_col = next((c for c in cols if c.strip().lower() in ("lieux", "lieu", "places", "locations")), None)
                lieux_raw = str(row.get(lieux_col, "")).strip() if lieux_col else ""
                lieux = [l.strip() for l in re.split(r"[;,]", lieux_raw) if l.strip()] if lieux_raw else []
                res = _upsert_region(settings_obj, region_key, region_acro, lieux)
                if res["created"]:
                    added_regions += 1
                if res["acr_updated"]:
                    updated_acronymes += 1
                added_lieux += res["new_lieux"]
                if res["created"] is False and (res["acr_updated"] or res["new_lieux"] > 0):
                    updated_regions += 1
            else:
                # region_col contains full name
                region_name = str(row.get(region_col, "")).strip() if region_col else ""
                if not region_name:
                    continue
                acr = str(row.get(short_col, "")).strip() if short_col else ""
                lieux_col = next((c for c in cols if c.strip().lower() in ("lieux", "lieu", "places", "locations")), None)
                lieux_raw = str(row.get(lieux_col, "")).strip() if lieux_col else ""
                lieux = [l.strip() for l in re.split(r"[;,]", lieux_raw) if l.strip()] if lieux_raw else []
                res = _upsert_region(settings_obj, region_name, acr, lieux)
                if res["created"]:
                    added_regions += 1
                if res["acr_updated"]:
                    updated_acronymes += 1
                added_lieux += res["new_lieux"]
                if res["created"] is False and (res["acr_updated"] or res["new_lieux"] > 0):
                    updated_regions += 1

    # --- Types (upsert simple) ---
    type_candidates = ("type", "type_borne", "type_bornes", "type_de_borne", "type(s)")
    sheet_t, df_t = _find_sheet_with_column(xls, type_candidates)
    if sheet_t and df_t is not None:
        df_t = df_t.fillna("")
        cols = [str(c).strip() for c in df_t.columns]
        type_col = next((c for c in cols if c.strip().lower() in type_candidates), None)
        if not type_col and cols:
            type_col = cols[0]
        if type_col:
            existing_types = settings_obj.setdefault("types_borne", [])
            for v in df_t[type_col].tolist():
                t = str(v).strip()
                if t and t not in existing_types:
                    existing_types.append(t)
                    added_types += 1

    _normalize_settings(settings_obj)
    return {
        "added_regions": added_regions,
        "updated_regions": updated_regions,
        "added_lieux": added_lieux,
        "updated_acronymes": updated_acronymes,
        "added_types": added_types
    }


# -----------------------
# Navigation (sous-menu simple) + uploader discret pour préremplir (upsert)
# -----------------------
st.sidebar.title("Paramètres")
st.sidebar.markdown("### Préremplir depuis Excel (optionnel)")
uploaded_init_xlsx = st.sidebar.file_uploader("Charger CONSO_CUPRA.xlsx", type=["xlsx", "xls"], key="uploader_init", help="Fichier Excel contenant colonnes 'Region' et/ou 'Type'")
if uploaded_init_xlsx is not None:
    try:
        preview = import_preview_from_excel(uploaded_init_xlsx)
        st.sidebar.write("Feuilles détectées :", preview["sheets"])
        if preview["regions_df"] is not None:
            st.sidebar.markdown(f"**Aperçu Regions (onglet détecté: {preview['regions_sheet']})**")
            st.sidebar.dataframe(preview["regions_df"])
            if preview["regions_are_acro"]:
                st.sidebar.info("La colonne détectée semble contenir des acronymes (seuil 80%). L'acronyme sera utilisé comme clé.")
        else:
            st.sidebar.info("Aucune feuille contenant une colonne 'Region' détectée.")
        if preview["types_df"] is not None:
            st.sidebar.markdown(f"**Aperçu Types (onglet détecté: {preview['types_sheet']})**")
            st.sidebar.dataframe(preview["types_df"])
        else:
            st.sidebar.info("Aucune feuille contenant une colonne 'Type' détectée.")
        if st.sidebar.button("Préremplir les listes depuis ce fichier"):
            uploaded_init_xlsx.seek(0)
            summary = apply_import_from_excel_upsert(uploaded_init_xlsx, settings)
            msg = (f"Préremplissage appliqué : +{summary['added_regions']} régions créées, "
                   f"{summary['updated_regions']} régions mises à jour, +{summary['added_lieux']} lieux ajoutés, "
                   f"{summary['updated_acronymes']} acronymes mis à jour, +{summary['added_types']} types ajoutés.")
            persist_and_notify(settings, msg)
            render_regions_table()
            render_types_list()
            _lieux_list_container.empty()
    except Exception as e:
        st.sidebar.error(f"Erreur lecture Excel : {e}")

section = st.sidebar.radio("Choisir la liste à modifier", ("Régions", "Lieux (par région)", "Types de borne"))

# -----------------------
# Section: Régions (création / renommage / suppression)
# -----------------------
def section_regions(settings):
    st.header("Régions")
    render_regions_table()
    _types_list_container.empty()
    _lieux_list_container.empty()

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
                    render_regions_table()
                    persist_and_notify(settings, f"Région '{key}' ajoutée.")

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
                render_regions_table()
                persist_and_notify(settings, "Région mise à jour.")

    st.markdown("#### Supprimer la région")
    if st.button("Supprimer cette région", key=f"del_region_{sel_region}"):
        confirm = st.checkbox(f"Confirmer la suppression de la région '{sel_region}'")
        if confirm:
            settings["regions"].pop(sel_region, None)
            render_regions_table()
            _lieux_list_container.empty()
            persist_and_notify(settings, f"Région '{sel_region}' supprimée.")


# -----------------------
# Section: Lieux (gestion par région)
# -----------------------
def section_lieux(settings):
    st.header("Lieux (par région)")
    regions_list = list(settings.get("regions", {}).keys())
    if not regions_list:
        st.info("Aucune région définie. Créez d'abord une région.")
        _regions_table_container.empty()
        _types_list_container.empty()
        _lieux_list_container.empty()
        return

    sel_region = st.selectbox("Choisir une région", [""] + regions_list, key="select_lieux_region")
    if not sel_region:
        _lieux_list_container.empty()
        _regions_table_container.empty()
        _types_list_container.empty()
        return

    st.subheader(f"Lieux pour {sel_region}")
    render_lieux_list(sel_region)
    _regions_table_container.empty()
    _types_list_container.empty()

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
                    render_regions_table()
                    render_lieux_list(sel_region)
                    persist_and_notify(settings, f"Lieu '{nl}' ajouté à {sel_region}.")

    st.markdown("### Supprimer des lieux")
    lieux = settings["regions"][sel_region].get("lieux", [])
    if lieux:
        to_remove = st.multiselect("Sélectionner les lieux à supprimer", options=lieux, key=f"multisel_{sel_region}")
        if st.button("Supprimer les lieux sélectionnés"):
            if to_remove:
                settings["regions"][sel_region]["lieux"] = [l for l in lieux if l not in to_remove]
                render_regions_table()
                render_lieux_list(sel_region)
                persist_and_notify(settings, f"{len(to_remove)} lieu(x) supprimé(s).")
            else:
                st.warning("Aucun lieu sélectionné.")


# -----------------------
# Section: Types de borne
# -----------------------
def section_types(settings):
    st.header("Types de borne")
    render_types_list()
    _regions_table_container.empty()
    _lieux_list_container.empty()

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
                    render_types_list()
                    persist_and_notify(settings, f"Type '{nt}' ajouté.")

    st.markdown("### Supprimer un type de borne")
    if settings.get("types_borne"):
        rem = st.multiselect("Sélectionner les types à supprimer", options=settings["types_borne"], key="multisel_types")
        if st.button("Supprimer les types sélectionnés"):
            if rem:
                settings["types_borne"] = [t for t in settings["types_borne"] if t not in rem]
                render_types_list()
                persist_and_notify(settings, f"{len(rem)} type(s) supprimé(s).")
            else:
                st.warning("Aucun type sélectionné.")


# -----------------------
# Dispatcher: afficher la section choisie
# -----------------------
if section == "Régions":
    section_regions(settings)
elif section == "Lieux (par région)":
    section_lieux(settings)
elif section == "Types de borne":
    section_types(settings)

# -----------------------
# Exécute le rerun si demandé (sécurisé)
# -----------------------
if st.session_state.get("_need_rerun", False):
    st.session_state["_need_rerun"] = False
    if hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()
        except Exception:
            st.session_state["_refresh_toggle"] = not st.session_state.get("_refresh_toggle", False)
    else:
        st.session_state["_refresh_toggle"] = not st.session_state.get("_refresh_toggle", False)
