import time
from shared.constants import COMFY_BASE_PATH
import streamlit as st
import os
import requests
import shutil
from zipfile import ZipFile
from io import BytesIO
from ui_components.constants import CreativeProcessType
from ui_components.methods.video_methods import upscale_video
from ui_components.widgets.inspiration_engine import inspiration_engine_element
from ui_components.widgets.timeline_view import timeline_view
from ui_components.components.explorer_page import gallery_image_view
from utils import st_memory
from utils.data_repo.data_repo import DataRepo

from ui_components.widgets.sidebar_logger import sidebar_logger
from ui_components.components.explorer_page import generate_images_element


def upscaling_page(shot_uuid: str, h2):

    with st.sidebar:
        with st.expander("🔍 Generation log", expanded=True):
            # if st_memory.toggle("Open", value=True, key="generaton_log_toggle"):
            sidebar_logger(st.session_state["shot_uuid"])
    
    list_of_videos = ["https://www.youtube.com/watch?v=dQw4w9WgXcQ","https://www.youtube.com/watch?v=dQw4w9WgXcQ","https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    st.markdown(f"#### :green[{st.session_state['main_view_type']}] > :red[{st.session_state['page']}]")
    st.markdown("***")
    slider1, slider2, slider3 = st.columns([2, 1, 1])
    with slider1:
        st.markdown("### ✨ Upscale videos")
        st.write("##### _\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_")
    st.write("")
    st.write("")
    
    def display_video(video_url, index):        
        
        vid1, vid2 = st.columns([1, 2])

        with vid1:
            st.markdown(f"#### From shot 'Mars Attack'")

            st.button("Remove from shortlist",key=f"remove_{index}", use_container_width=True)
            st.markdown("***") 
            status = st.radio("Status (for demo purposes)", ["Non-upscaled", "Upscaled","Upscale in progress"],key=f"status_{index}", horizontal=True)
            
            if status == "Upscaled":
                st.success("Upscaled video")
            elif status == "Upscale in progress":
                st.info("Upscale pending")
            else:
                checkpoints_dir = os.path.join(COMFY_BASE_PATH, "models", "checkpoints")
                all_files = os.listdir(checkpoints_dir)
                if len(all_files) == 0:
                    st.info("No models found in the checkpoints directory")
                    styling_model = "None"
                else:
                    
                    with st.expander("Upscale settings"):
                        # Filter files to only include those with .safetensors and .ckpt extensions
                        model_files = [file for file in all_files if file.endswith(".safetensors") or file.endswith(".ckpt")]
                        # drop all files that contain xl
                        model_files = [file for file in model_files if "xl" not in file]
                        # model_files.insert(0, "None")  # Add "None" option at the beginning
                        styling_model = st.selectbox("Styling model", model_files, key=f"styling_model_{index}")

                        upscale_by = st.slider("Upscale by", min_value=1.0, max_value=3.0, step=0.1, key=f"upscale_by_{index}", value=1.5)

                st.button("Queue for upscaling",key=f"queue_{index}",use_container_width=True,type="primary")                                            

            
        with vid2:        
            if status == "Upscaled":
                st.success("SHOW UPSCALED VIDEO HERE")
            st.video(video_url)
            st.button("Download",key=f"download_{index}",use_container_width=True)

    
    main_clip_list = [1,2,3,4,5]
    
    with slider3:
        with st.expander("Export all shortlisted videos", expanded=False):
            if not len(main_clip_list):
                st.info("No videos available in the project.")

            else:
                if st.button("Prepare videos for download"):
                    temp_dir = "temp_main_variants"
                    os.makedirs(temp_dir, exist_ok=True)
                    zip_data = BytesIO()
                    st.info("Preparing videos for download. This may take a while.")
                    time.sleep(0.4)
                    try:
                        for idx, shot in enumerate(shot_list):
                            if shot.main_clip and shot.main_clip.location:
                                # Prepend the shot number (idx + 1) to the filename
                                file_name = f"{idx + 1:03d}_{shot.name}.mp4"  # Using :03d to ensure the number is zero-padded to 3 digits
                                file_path = os.path.join(temp_dir, file_name)
                                if shot.main_clip.location.startswith("http"):
                                    response = requests.get(shot.main_clip.location)
                                    with open(file_path, "wb") as f:
                                        f.write(response.content)
                                else:
                                    shutil.copyfile(shot.main_clip.location, file_path)

                        with ZipFile(zip_data, "w") as zipf:
                            for root, _, files in os.walk(temp_dir):
                                for file in files:
                                    zipf.write(os.path.join(root, file), file)

                        st.download_button(
                            label="Download Main Variant Videos zip",
                            data=zip_data.getvalue(),
                            file_name="main_variant_videos.zip",
                            mime="application/zip",
                            key="main_variant_download",
                            use_container_width=True,
                            type="primary",
                        )
                    finally:
                        shutil.rmtree(temp_dir)

    with slider2:
        with st.expander("Bulk upscale", expanded=False):

            def upscale_settings():
                checkpoints_dir = os.path.join(COMFY_BASE_PATH, "models", "checkpoints")
                all_files = os.listdir(checkpoints_dir)
                if len(all_files) == 0:
                    st.info("No models found in the checkpoints directory")
                    styling_model = "None"
                else:
                    # Filter files to only include those with .safetensors and .ckpt extensions
                    model_files = [
                        file
                        for file in all_files
                        if file.endswith(".safetensors") or file.endswith(".ckpt")
                    ]
                    # drop all files that contain xl
                    model_files = [file for file in model_files if "xl" not in file]
                    # model_files.insert(0, "None")  # Add "None" option at the beginning
                    styling_model = st.selectbox("Styling model:", model_files, key="styling_model")

                upscale_by = st.slider(
                    "Upscale by:", min_value=1.0, max_value=3.0, step=0.1, key="upscale_by", value=1.5
                )
                set_upscaled_to_main_variant = True

                return (
                    styling_model,
                    upscale_by,
                    set_upscaled_to_main_variant,
                )

            if not len(main_clip_list):
                st.info("No videos to upscale")
            else:
                (
                    styling_model,
                    upscale_factor,
                    promote_to_main_variant,
                ) = upscale_settings()
                if st.button("Upscale All shortlisted clips"):
                    for shot in shot_list:
                        if shot.main_clip and shot.main_clip.location:
                            upscale_video(
                                shot.main_clip.uuid,
                                shot.uuid,
                                styling_model,
                                upscale_factor,
                                promote_to_main_variant,
                            )
        
    
    if list_of_videos:                        
        ## display 2 per row
        for i in range(0,len(list_of_videos),2):
            col1, col2 = st.columns(2)
            with col1:
                display_video(list_of_videos[i],i)
            with col2:
                if i+1 < len(list_of_videos):
                    display_video(list_of_videos[i+1],i+1)
            st.markdown("***")

    else:
        st.info("You need to shortlist videos on the Adjust Shot view for them to appear here.")