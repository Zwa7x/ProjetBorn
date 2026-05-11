# pages/5_🛠️_Settings.py
import streamlit as st
import pandas as pd
import traceback
from utils import load_settings, save_settings

st.set_page_config(page_title="⚙️ Paramètres", layout="wide")
st.title("⚙️ Paramètres de l'application")

# -----------------------
# Petit CSS pour ajustements visuels
# -----------------------
st.markdown(
    """
    <style>
    /* réduire la largeur de la première colonne (case Supprimer) dans les tableaux */
    .stDataFrame table th:first-child,
    .stDataFrame table td:first-child,
    .streamlit-expanderContent table th:first-child,
    .streamlit-expanderContent table td:first-child {
        width: 48px !important;
        max-width: 48px !important;
        text-align: center;
    }
    /* si data_editor génère une table différente */
    div[data-testid="stDataFrameContainer"] table th:first-child,
    div[data-testid="stDataFrameContainer"] table td:first-child {
        width: 48px !important;
        max-width: 48px !important;
        text-align: center;
    }
    /* réduire la police du titre d'édition rapide */
    .small-edit-title {
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
        color: #111827;
    }
    /* bouton menu contextuel aligné à droite */
    .top-right-menu {
        display:flex;
        justify-content:flex-end;
        gap:8px;
        margin-bottom:8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
# Helpers utilitaires
# -----------------------
def settings_to_regions_df(s):
    rows = []
    for name, meta in (s.get("regions") or {}).items():
        if isinstance(meta, dict):
            acr = meta.get("acronyme", "") or ""
            lieux = meta.get("lieux", []) or []
            lieux_str = ", ".join(lieux)
        else:
            acr = ""
            lieux_str = str(meta)
        rows.append({"Supprimer": False, "Région": name, "Acronyme": acr, "Lieux (séparés par ,)": lieux_str})
    if not rows:
        return pd.DataFrame(columns=["Supprimer", "Région", "Acronyme", "Lieux (séparés par ,)"])
    return pd.DataFrame(rows)

def df_to_settings_regions(df, base_settings):
    regs = {}
    for _, row in df.iterrows():
        # ignorer les lignes marquées Supprimer
        try:
            if bool(row.get("Supprimer")):
                continue
        except Exception:
            pass
        name = str(row.get("Région") or "").strip()
        if not name:
            continue
        acr = str(row.get("Acronyme") or "").strip()
        lieux_raw = str(row.get("Lieux (séparés par ,)") or "").strip()
        if lieux_raw:
            lieux = [l.strip() for l in lieux_raw.split(",") if l.strip()]
        else:
            lieux = []
        existing = (base_settings.get("regions") or {}).get(name, {})
        if isinstance(existing, dict):
            regs[name] = {"acronyme": acr or existing.get("acronyme", ""), "lieux": list(dict.fromkeys(lieux or existing.get("lieux", [])))}
        else:
            regs[name] = {"acronyme": acr, "lieux": lieux}
    return regs

def safe_save_and_rerun(s, msg="Sauvegarde effectuée"):
    try:
        save_settings(s)
        st.success(msg)
        if hasattr(st, "experimental_rerun"):
            try:
                st.experimental_rerun()
            except Exception:
                st.session_state["_refresh_toggle"] = not st.session_state.get("_refresh_toggle", False)
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")
        st.text(traceback.format_exc())

# -----------------------
# Initialisation du DataFrame éditable dans session_state
# -----------------------
if "regions_df" not in st.session_state:
    st.session_state["regions_df"] = settings_to_regions_df(settings)

# -----------------------
# Top: tableau récapitulatif éditable (Regions) avec colonne Supprimer
# -----------------------
st.markdown("## Récapitulatif des régions")
st.markdown("Édite directement les cellules. **Région** est la clé principale. Coche **Supprimer** pour retirer une ligne puis cliquez sur **Appliquer**.")

# Affichage éditable (data_editor si dispo)
data_editor = getattr(st, "data_editor", None) or getattr(st, "experimental_data_editor", None)
if data_editor:
    edited = data_editor(st.session_state["regions_df"], use_container_width=True, key="regions_data_editor")
    try:
        if isinstance(edited, pd.DataFrame):
            st.session_state["regions_df"] = edited
        else:
            st.session_state["regions_df"] = pd.DataFrame(edited)
    except Exception:
        pass
else:
    st.warning("Édition inline non disponible dans cette version de Streamlit.")
    st.dataframe(st.session_state["regions_df"], use_container_width=True)

# -----------------------
# Menu contextuel en haut à droite (Ajouter / Supprimer / Appliquer / Annuler)
# -----------------------
# On crée une ligne avec un espace à gauche et le menu à droite
left, right = st.columns([3, 1])
with right:
    st.markdown('<div class="top-right-menu">', unsafe_allow_html=True)
    add_row = st.button("➕ Ajouter ligne", key="ctx_add_row")
    del_selected = st.button("🗑️ Suppr. sélection", key="ctx_del_sel")
    apply_table = st.button("✅ Appliquer", key="ctx_apply")
    cancel_table = st.button("↺ Annuler", key="ctx_cancel")
    st.markdown('</div>', unsafe_allow_html=True)

# Actions du menu contextuel
if add_row:
    df = st.session_state.get("regions_df", pd.DataFrame(columns=["Supprimer", "Région", "Acronyme", "Lieux (séparés par ,)"]))
    new_row = pd.DataFrame([{"Supprimer": False, "Région": "", "Acronyme": "", "Lieux (séparés par ,)": ""}])
    st.session_state["regions_df"] = pd.concat([df, new_row], ignore_index=True)
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

if del_selected:
    # supprime les lignes cochées Supprimer dans le DataFrame
    df = st.session_state.get("regions_df", pd.DataFrame())
    if "Supprimer" in df.columns:
        try:
            df["Supprimer"] = df["Supprimer"].astype(bool)
            if df["Supprimer"].any():
                df = df[~df["Supprimer"]].reset_index(drop=True)
                st.session_state["regions_df"] = df
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
            else:
                st.warning("Aucune ligne cochée pour suppression.")
        except Exception:
            st.warning("Impossible d'interpréter la colonne Supprimer.")
    else:
        st.warning("Aucune colonne Supprimer trouvée.")

if apply_table:
    try:
        df = st.session_state.get("regions_df", pd.DataFrame())
        if "Supprimer" in df.columns:
            df["Supprimer"] = df["Supprimer"].astype(bool)
        new_regions = df_to_settings_regions(df, settings)
        settings["regions"] = new_regions
        safe_save_and_rerun(settings, "Modifications des régions appliquées.")
    except Exception as e:
        st.error("Erreur lors de l'application : " + str(e))
        st.text(traceback.format_exc())

if cancel_table:
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        st.session_state["_refresh_toggle"] = not st.session_state.get("_refresh_toggle", False)

st.markdown("---")

# -----------------------
# Bloc d'édition sous le tableau (titre plus discret)
# -----------------------
st.markdown('<div class="small-edit-title"><strong>Édition rapide d\'une région</strong></div>', unsafe_allow_html=True)
regions_list = sorted(list(settings.get("regions", {}).keys()))
if not regions_list:
    st.info("Aucune région définie. Ajoute d'abord une région dans le tableau ci‑dessus.")
else:
    sel = st.selectbox("Sélectionner une région à éditer", [""] + regions_list, key="select_region_edit")
    if sel:
        meta = settings["regions"].get(sel, {"acronyme": "", "lieux": []})
        with st.form(f"form_edit_region_{sel}"):
            new_name = st.text_input("Nom de la région", sel, key=f"edit_name_{sel}")
            new_acro = st.text_input("Acronyme", meta.get("acronyme", ""), key=f"edit_acro_{sel}")
            lieux_str = ", ".join(meta.get("lieux", []) or [])
            new_lieux = st.text_area("Lieux (séparés par des virgules)", lieux_str, key=f"edit_lieux_{sel}")
            col_save, col_delete = st.columns([1,1])
            with col_save:
                if st.form_submit_button("Enregistrer les modifications"):
                    nm = new_name.strip()
                    if not nm:
                        st.warning("Le nom de la région ne peut pas être vide.")
                    else:
                        if nm != sel and nm in settings.get("regions", {}):
                            st.warning("Une région avec ce nom existe déjà.")
                        else:
                            lieux_list = [l.strip() for l in new_lieux.split(",") if l.strip()]
                            if nm != sel:
                                settings["regions"][nm] = settings["regions"].pop(sel)
                                sel = nm
                            settings["regions"][sel]["acronyme"] = new_acro.strip()
                            settings["regions"][sel]["lieux"] = lieux_list
                            st.session_state["regions_df"] = settings_to_regions_df(settings)
                            safe_save_and_rerun(settings, f"Région '{sel}' mise à jour.")
            with col_delete:
                if st.form_submit_button("Supprimer cette région"):
                    confirm = st.checkbox(f"Confirmer suppression de '{sel}'", key=f"confirm_del_{sel}")
                    if confirm:
                        settings["regions"].pop(sel, None)
                        st.session_state["regions_df"] = settings_to_regions_df(settings)
                        safe_save_and_rerun(settings, f"Région '{sel}' supprimée.")

st.markdown("---")

# -----------------------
# Section Lieux (dédiée)
# -----------------------
st.markdown("## Lieux (par région)")
regions_list = sorted(list(settings.get("regions", {}).keys()))
if not regions_list:
    st.info("Aucune région définie. Ajoute d'abord une région dans le tableau ci‑dessus.")
else:
    col_l1, col_l2 = st.columns([2,1])
    with col_l1:
        sel_region = st.selectbox("Choisir une région", [""] + regions_list, key="select_lieux_region")
        if sel_region:
            st.subheader(f"Lieux pour {sel_region}")
            lieux = settings["regions"].get(sel_region, {}).get("lieux", []) or []
            if lieux:
                df_lieux = pd.DataFrame({"Lieu": lieux})
                st.dataframe(df_lieux, use_container_width=True)
            else:
                st.info("Aucun lieu pour cette région.")

            with st.form(f"form_add_lieu_{sel_region}", clear_on_submit=True):
                new_lieu = st.text_input("Ajouter un lieu", "")
                if st.form_submit_button("Ajouter le lieu"):
                    nl = new_lieu.strip()
                    if not nl:
                        st.warning("Nom du lieu requis.")
                    else:
                        if nl in settings["regions"][sel_region].get("lieux", []):
                            st.warning("Ce lieu existe déjà pour la région.")
                        else:
                            settings["regions"][sel_region].setdefault("lieux", []).append(nl)
                            st.session_state["regions_df"] = settings_to_regions_df(settings)
                            safe_save_and_rerun(settings, f"Lieu '{nl}' ajouté à {sel_region}.")

    with col_l2:
        st.markdown("### Supprimer des lieux")
        if sel_region:
            lieux = settings["regions"].get(sel_region, {}).get("lieux", []) or []
            if lieux:
                to_remove = st.multiselect("Sélectionner les lieux à supprimer", options=lieux, key=f"multisel_lieux_{sel_region}")
                if st.button("Supprimer les lieux sélectionnés", key=f"btn_del_lieux_{sel_region}"):
                    if to_remove:
                        settings["regions"][sel_region]["lieux"] = [l for l in lieux if l not in to_remove]
                        st.session_state["regions_df"] = settings_to_regions_df(settings)
                        safe_save_and_rerun(settings, f"{len(to_remove)} lieu(x) supprimé(s) de {sel_region}.")
                    else:
                        st.warning("Aucun lieu sélectionné.")
            else:
                st.info("Aucun lieu à supprimer pour cette région.")

st.markdown("---")

# -----------------------
# Section Types de borne
# -----------------------
st.markdown("## Types de borne")
tb = settings.get("types_borne", []) or []
def tb_label(t):
    return t if isinstance(t, str) else (t.get("label") or t.get("code") or str(t))

if tb:
    df_tb = pd.DataFrame({"Type": [tb_label(t) for t in tb]})
    st.dataframe(df_tb, use_container_width=True)
else:
    st.info("Aucun type de borne défini.")

with st.form("form_add_type", clear_on_submit=True):
    new_type = st.text_input("Ajouter un type (ex: AC 22kW)", "")
    if st.form_submit_button("Ajouter le type"):
        nt = new_type.strip()
        if not nt:
            st.warning("Libellé requis.")
        else:
            existing_labels = [tb_label(t) for t in settings.setdefault("types_borne", [])]
            if nt in existing_labels:
                st.warning("Ce type existe déjà.")
            else:
                settings["types_borne"].append(nt)
                safe_save_and_rerun(settings, f"Type '{nt}' ajouté.")
if settings.get("types_borne"):
    options = [tb_label(t) for t in settings["types_borne"]]
    rem = st.multiselect("Sélectionner les types à supprimer", options=options, key="multisel_types_main")
    if st.button("Supprimer les types sélectionnés"):
        if rem:
            settings["types_borne"] = [t for t in settings["types_borne"] if tb_label(t) not in rem]
            safe_save_and_rerun(settings, f"{len(rem)} type(s) supprimé(s).")
        else:
            st.warning("Aucun type sélectionné.")

st.markdown("---")
st.write("Debug rapide: nombre de régions =", len(settings.get("regions", {})), " | types =", len(settings.get("types_borne", [])))
