# recording.py

import streamlit as st
import asyncio
from amazon_transcribe.client import TranscribeStreamingClient
from handlers import TranscriptResultStreamHandler  # Ensure absolute import
import sounddevice as sd
import threading
import boto3
import io
import requests
from ai_agent import ai_agent_clean, ai_agent_summary  # Correct import based on file name

def handle_recording(folder_name, bucket_name):
    """
    Handles the Start Recording and Stop Recording buttons and the transcription process.
    """
    # Arrange the Start Recording and Stop Recording buttons side by side
    record_col1, record_col2 = st.columns(2)

    with record_col2:
        start_button_clicked = st.button("התחל הקלטה ▶️") and not st.session_state.show_buttons
        if start_button_clicked:
            st.session_state.recording = True
            st.markdown("<div class='status-message'>מתחיל הקלטה ותמלול - אפשר להתחיל לדבר.</div>", unsafe_allow_html=True)
            # Define the transcription placeholder below the buttons
            transcription_placeholder = st.empty()
            # Run the transcription asynchronously
            handler = asyncio.run(basic_transcribe(transcription_placeholder))

            # Start silent recording
            start_recording()
            st.write("ההקלטה החלה")  # "Recording started"

    with record_col1:
        stop_button_clicked = st.button("עצור הקלטה ⏹️") and st.session_state.recording and not st.session_state.show_buttons
        if stop_button_clicked:
            st.session_state.recording = False
            st.markdown("<p style='direction: rtl; text-align: right;'>התמלול הופסק.</p>", unsafe_allow_html=True)  # "Transcription stopped."

            # Stop recording and upload the audio
            stop_recording_and_upload(folder_name, bucket_name)

            # Process the transcription
            process_transcription(folder_name, bucket_name)


def process_transcription(folder_name, bucket_name):
    """
    Processes the transcription by displaying raw text, cleaning, summarizing, and uploading to S3.
    """
    raw_text = st.session_state.transcription_text
    if not raw_text:
        st.error("אין תמלול זמין לעיבוד.")  # "No transcription available for processing."
        return

    # Display the raw transcription
    st.text_area(
        "תמלול מקורי",
        value=raw_text,
        height=150,
        key="raw_text_area",
        disabled=True
    )
    st.success("מבצע טעינת נתונים - נא המתינו להשלמת שלושת השלבים")

    # Define S3 keys
    raw_text_key = f"{folder_name}/raw.txt"
    clean_text_key = f"{folder_name}/clean.txt"
    summary_text_key = f"{folder_name}/summary.txt"

    # Upload raw text to S3
    try:
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.put_object(
            Bucket=bucket_name,
            Key=raw_text_key,
            Body=raw_text,
            ContentType='text/plain'
        )
        st.write(f"S3 Path: {raw_text_key}")
        st.write("שלב 1 הושלם בהצלחה")  # "Step 1 completed successfully"
    except Exception as e:
        st.error(f"טעינת התמלול הגולמי נכשלה: {e}")  # "Uploading raw transcription failed: {error}"
        return

    # Clean the transcription
    try:
        with st.spinner('מנקה את התמלול...'):
            clean_text = ai_agent_clean(raw_text)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=clean_text_key,
            Body=clean_text,
            ContentType='text/plain'
        )
        st.write(f"Clean Text S3 Path: {clean_text_key}")
        st.write("שלב 2 הושלם בהצלחה")  # "Step 2 completed successfully"
    except Exception as e:
        st.error(f"ניקוי התמלול נכשל: {e}")  # "Cleaning transcription failed: {error}"
        return

    # Summarize the transcription
    try:
        with st.spinner('מסכם את התמלול...'):
            summary_text = ai_agent_summary(clean_text)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=summary_text_key,
            Body=summary_text,
            ContentType='text/plain'
        )
        st.write(f"Summary Text S3 Path: {summary_text_key}")
        st.write("שלב 3 הושלם בהצלחה")  # "Step 3 completed successfully"
    except Exception as e:
        st.error(f"סיכום התמלול נכשל: {e}")  # "Summarizing transcription failed: {error}"
        return

    # Final success message
    st.success("התמלול מוכן - כעת ניתן להציג את סיכום שיחה")  # "Transcription is ready - you can now view the conversation summary"
    st.markdown("<div class='status-message'>ההקלטה הסתיימה</div>", unsafe_allow_html=True)

    # Show buttons after processing
    st.session_state.show_buttons = True

def start_recording():
    """
    Starts recording audio in a separate thread and saves it to session state.
    """
    st.session_state.recording = True
    # Start recording in a separate thread
    def record():
        with sd.InputStream(samplerate=16000, channels=1, dtype='int16') as stream:
            while st.session_state.recording:
                data, _ = stream.read(1024)
                st.session_state.audio_buffer.write(data.tobytes())
    threading.Thread(target=record, daemon=True).start()

def stop_recording_and_upload(folder_name, bucket_name):
    """
    Stops the recording, uploads the audio to S3, and resets the buffer.
    """
    st.session_state.recording = False
    # Convert the recorded bytes to MP3 (requires additional processing if needed)
    audio_data = st.session_state.audio_buffer.getvalue()
    s3_record = f"{folder_name}/record.mp3"
    try:
        with st.spinner('מעלה את ההקלטה ל-S3...'):
            s3_client = boto3.client('s3', region_name='us-east-1')
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_record,
                Body=audio_data,
                ContentType='audio/mpeg'
            )
        st.success("ההקלטה הועלתה בהצלחה ל-S3.")  # "Audio recorded and uploaded to S3 successfully."
    except Exception as e:
        st.error(f"לא ניתן להעלות את ההקלטה: {e}")  # "Could not upload audio: {error}"
    # Reset the buffer
    st.session_state.audio_buffer = io.BytesIO()

# Event handler class
class MyEventHandler(TranscriptResultStreamHandler):
    def __init__(self, stream, transcription_display):
        super().__init__(stream)
        self.transcription_display = transcription_display
        self.transcription_accum = ""
        self.event_count = 0
        self.stop_transcription = False

    async def handle_transcript_event(self, transcript_event):
        if self.stop_transcription:
            return

        results = transcript_event.transcript.results
        self.event_count += 1
        for result in results:
            speaker = None
            if result.alternatives[0].items[0].speaker is not None:
                speaker = f"דובר {result.alternatives[0].items[0].speaker}: "  # Hebrew "Speaker"
                # speaker = f"{result.alternatives[0].items[0].speaker}: "  # Hebrew "Speaker"

            if len(result.alternatives) > 0:
                transcript = result.alternatives[0].transcript
                full_transcript = f"{speaker}{transcript}" if speaker else transcript

                # Check if this is a partial result or a final result
                if not result.is_partial:
                    # For final results, append the full transcript
                    self.transcription_accum += full_transcript + "\n"
                    self.transcription_display.text_area(
                        "תמלול:",
                        self.transcription_accum,
                        height=300,
                        key=f"live_{self.event_count}"
                    )
                    # Store the accumulated transcription in session state
                    st.session_state.transcription_text = self.transcription_accum
                else:
                    # For partial results, update the last line
                    lines = self.transcription_accum.split('\n')
                    if lines[-1].strip():  # If the last line is not empty
                        lines[-1] = full_transcript
                    else:
                        lines.append(full_transcript)

                    self.transcription_show = '\n'.join(lines)

                    # Update transcription display in Streamlit
                    self.transcription_display.text_area(
                        "תמלול:",
                        self.transcription_show,
                        height=300,
                        key=f"live_{self.event_count}"
                    )

async def mic_stream():
    loop = asyncio.get_event_loop()
    input_queue = asyncio.Queue()

    def callback(indata, frame_count, time_info, status):
        loop.call_soon_threadsafe(input_queue.put_nowait, (bytes(indata), status))

    stream = sd.RawInputStream(
        channels=1,
        samplerate=16000,
        callback=callback,
        blocksize=1024 * 2,
        dtype="int16"
    )

    with stream:
        while True:
            indata, status = await input_queue.get()
            yield indata, status

async def write_chunks(stream, handler):
    async for chunk, status in mic_stream():
        if handler.stop_transcription:
            break
        await stream.input_stream.send_audio_event(audio_chunk=chunk)
    await stream.input_stream.end_stream()

async def basic_transcribe(transcription_display):
    client = TranscribeStreamingClient(region="us-east-1")  # Corrected region

    stream = await client.start_stream_transcription(
        language_code="he-IL",
        media_sample_rate_hz=16000,
        media_encoding="pcm",
        show_speaker_label=True
    )

    handler = MyEventHandler(stream.output_stream, transcription_display)

    # Create a task for handling events
    event_task = asyncio.create_task(handler.handle_events())

    # Create a task for writing chunks
    chunk_task = asyncio.create_task(write_chunks(stream, handler))

    # Wait for both tasks to complete
    await asyncio.gather(event_task, chunk_task)

    return handler
