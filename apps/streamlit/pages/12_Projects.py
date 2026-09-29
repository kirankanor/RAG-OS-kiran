import sys
from pathlib import Path
import streamlit as st
from sqlmodel import select
sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.documents.application.queries.list_documents import ListDocumentsQuery
from modules.experiments.application.services.experiment_service import ExperimentService
from modules.projects.application.commands.create_project import CreateProjectCommand
from modules.projects.application.commands.delete_project import DeleteProjectCommand
from modules.projects.application.commands.update_project import UpdateProjectCommand
from modules.projects.application.queries.list_projects import ListProjectsQuery
from modules.projects.domain.exceptions import InvalidProjectError, ProjectStateError
from modules.users.application.services.user_service import UserService
from modules.users.domain.exceptions import UserError
from modules.users.infrastructure.persistence.models import UserRow
from shared.infrastructure.database.db_models import get_session

st.set_page_config(page_title="Projects - RAG-OS", page_icon="\U0001F4CB", layout="wide")
st.title("\U0001F4CB Projects")
st.caption("Ties an owner to a set of documents and experiments.")


def list_users():
    with get_session() as session:
        return list(session.exec(select(UserRow).order_by(UserRow.email)))


users = list_users()
with st.expander("\U0001F464 Register a user (needed as a project owner)"):
    with st.form("register_user"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Register")
    if submitted:
        try:
            UserService().register(email, password)
            st.success(f"Registered {email}.")
            st.rerun()
        except UserError as e:
            st.error(str(e))

if not users:
    st.info("Register a user above to create a project.")
    st.stop()

docs = ListDocumentsQuery().execute()
experiments = ExperimentService().list()
user_label = {u.email: u.id for u in users}
doc_label = {f"{d.name} ({d.id})": d.id for d in docs}
exp_label = {f"{e.name} ({e.id})": str(e.id) for e in experiments}

with st.expander("\u2795 Create a project"):
    with st.form("create_project"):
        name = st.text_input("Name")
        description = st.text_area("Description", value="")
        owner_id = user_label[st.selectbox("Owner", options=list(user_label))]
        doc_ids = [doc_label[k] for k in st.multiselect("Documents", options=list(doc_label))]
        exp_ids = [exp_label[k] for k in st.multiselect("Experiments", options=list(exp_label))]
        submitted = st.form_submit_button("Create")
    if submitted:
        try:
            CreateProjectCommand().execute(name, owner_id, description, doc_ids, exp_ids)
            st.success(f"Created project '{name}'.")
            st.rerun()
        except InvalidProjectError as e:
            st.error("; ".join(e.errors) or str(e))

projects = ListProjectsQuery().execute()
if not projects:
    st.info("No projects yet — create one above.")
    st.stop()

for p in projects:
    with st.expander(f"{p.name} — {p.status}"):
        st.write(p.description or "_no description_")
        st.caption(f"id: `{p.id}`  ·  owner: `{p.owner_id}`  ·  "
                   f"{p.num_documents} doc(s), {p.num_experiments} experiment(s)")
        col1, col2, col3 = st.columns(3)
        if p.status == "active" and col1.button("Archive", key=f"arc_{p.id}"):
            UpdateProjectCommand().execute(p.id, archived=True)
            st.rerun()
        if p.status == "archived" and col2.button("Unarchive", key=f"unarc_{p.id}"):
            try:
                UpdateProjectCommand().execute(p.id, archived=False)
                st.rerun()
            except ProjectStateError as e:
                st.error(str(e))
        if p.status != "deleted" and col3.button("Delete", key=f"del_{p.id}"):
            DeleteProjectCommand().execute(p.id)
            st.rerun()
