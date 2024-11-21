# handlers.py

from amazon_transcribe.handlers import TranscriptResultStreamHandler
import streamlit as st

class TranscriptResultStreamHandler(TranscriptResultStreamHandler):
    """
    Custom handler for processing transcription results.
    """

    async def handle_transcript_event(self, transcript_event):
        """
        Override this method to handle incoming transcription events.
        """
        pass  # Implement in recording.py or other modules as needed
