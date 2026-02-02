import streamlit.web.bootstrap
import os, sys

if __name__ == "__main__":
    # This ensures the app looks for files relative to the .exe location
    os.chdir(os.path.dirname(__file__))
    
    flag_options = {
        "server.port": 8501,
        "global.developmentMode": False,
    }
    
    # Replace 'your_main_script.py' with your actual filename
    streamlit.web.bootstrap.run('bird_app.py', '', [], flag_options)