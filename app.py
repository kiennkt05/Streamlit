import streamlit as st
import os
import yaml
import tempfile
import main
import sys
import io

# --- App Configuration ---
st.set_page_config(
    page_title="Dynamic UI Generator",
    page_icon="✨",
    layout="wide"
)

# --- Session State Initialization ---
# This dictionary will hold all the state for our internal router and data.
if 'app_state' not in st.session_state:
    st.session_state.app_state = {
        "view": "uploader",  # Can be 'uploader' or 'generated_app'
        "generated_code": None,
        "uploaded_file_name": None,
    }

# --- Helper Functions ---
def switch_view(view_name):
    """Function to switch the internal view."""
    st.session_state.app_state['view'] = view_name
    st.rerun()

# --- Main App Logic ---

# Use the 'view' from state to decide what to render
current_view = st.session_state.app_state['view']

# ==============================================================================
# VIEW 1: The Uploader Interface
# ==============================================================================
if current_view == "uploader":
    st.header("📤 Upload your Task.yaml File")
    
    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Choose your Task.yaml file",
            type=['yaml', 'yml'],
            help="Upload your Task.yaml file"
        )

    with col2:
        st.markdown("**Supported formats:**")
        st.markdown("• .yaml")
        st.markdown("**Contents**")
        if uploaded_file:
            st.markdown(f"• {uploaded_file.name}")
        else:
            st.markdown("• No file uploaded yet")

    st.markdown("---")

    if uploaded_file:
        st.subheader("🚀 Ready to Generate UI Code")
        
        if st.button("✨ Generate UI", type="primary", use_container_width=True):
            with st.spinner("Generating UI Code... This may take a moment."):
                try:
                    # Use a temporary file to pass to the main function
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
                        file_content = uploaded_file.read().decode('utf-8')
                        temp_file.write(file_content)
                        temp_yaml_path = temp_file.name

                    # Call main() to get the code as a string
                    generated_code_string = main.main(temp_yaml_path)
                    
                    # Clean up the temporary file
                    os.unlink(temp_yaml_path)

                    # Store the generated code in session state
                    st.session_state.app_state['generated_code'] = generated_code_string
                    
                    # Switch to the 'generated_app' view
                    switch_view('generated_app')

                except Exception as e:
                    st.error(f"❌ An error occurred during generation: {e}")
    else:
        st.info("📁 Please upload a Task.yaml file to continue")

# ==============================================================================
# VIEW 2: The Dynamically Generated App
# ==============================================================================
elif current_view == "generated_app":
    st.sidebar.button("⬅️ Back to Uploader", on_click=switch_view, args=('uploader',))
    st.sidebar.markdown("---")
    
    generated_code = st.session_state.app_state.get('generated_code')
    
    if generated_code:
        st.sidebar.subheader("📄 Generated Code")
        with st.sidebar.expander("Click to view the code running this page"):
            st.code(generated_code, language='python')
        
        try:
            # Prepare a namespace for execution.
            # We pass a dictionary of modules that the generated code might need.
            namespace = {
                "st": st,
                "os": os,
                "yaml": yaml,
                "tempfile": tempfile,
                # Add any other modules the LLM is likely to use
                "pandas": __import__("pandas"),
                "numpy": __import__("numpy"),
                "requests": __import__("requests"),
                "io": io,
                "PIL": __import__("PIL"),
                "librosa": __import__("librosa"),
            }
            # Execute the generated code within the prepared namespace
            exec(generated_code, namespace)
            
        except Exception as e:
            st.error(f"❌ An error occurred while running the generated code: {e}")
            st.code(generated_code, language='python')
    else:
        st.error("No generated code found.")
        st.button("Go back to uploader", on_click=switch_view, args=('uploader',))