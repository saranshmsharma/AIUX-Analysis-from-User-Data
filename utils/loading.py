import streamlit as st
import time
from typing import Generator, Optional

class LoadingAnimation:
    def __init__(self):
        self.progress_placeholder = None
        self.status_placeholder = None
    
    def progress_bar(self, total_steps: int = 100) -> Generator[None, None, None]:
        """Show a custom progress bar"""
        progress = 0
        self.progress_placeholder = st.empty()
        
        while progress < total_steps:
            progress += 1
            self.progress_placeholder.progress(progress / total_steps)
            yield
            time.sleep(0.01)
            
        self.progress_placeholder.empty()

    def loading_spinner(self, text: str, success_text: Optional[str] = None) -> None:
        """Show a loading spinner with custom text"""
        with st.spinner(text):
            yield
        if success_text:
            st.success(success_text)
            time.sleep(0.5)

    def pulsing_status(self, messages: list) -> None:
        """Show pulsing status messages"""
        self.status_placeholder = st.empty()
        
        for message in messages:
            self.status_placeholder.info(message)
            yield
            time.sleep(0.8)
        
        self.status_placeholder.empty()

    def staged_loading(self, stages: dict) -> None:
        """Show staged loading process"""
        progress = st.progress(0)
        status = st.empty()
        
        total_stages = len(stages)
        for i, (stage_name, stage_desc) in enumerate(stages.items(), 1):
            status.info(f"{stage_name}: {stage_desc}")
            progress.progress(i / total_stages)
            yield
            time.sleep(0.5)
            
        progress.empty()
        status.empty() 