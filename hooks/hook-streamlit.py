from PyInstaller.utils.hooks import copy_metadata, collect_data_files

# This captures the version info and static assets (CSS/JS)
datas = copy_metadata('streamlit')
datas += collect_data_files('streamlit')