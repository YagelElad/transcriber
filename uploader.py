# uploader.py

import streamlit as st
import uuid
import boto3
import requests
import time
from dotenv import load_dotenv
from ai_agent import ai_agent_clean, ai_agent_summary  # Ensure correct import based on file name

def handle_uploader(folder_name, bucket_name):
    """
    Handles the file upload process via a checkbox and file uploader.
    """
    # Use a checkbox to toggle the file uploader
    show_upload = st.checkbox("העלה קובץ", key='toggle_upload')

    if show_upload and not st.session_state.show_buttons:
        uploaded_file = st.file_uploader(
            "בחר קובץ להעלאה",
            type=["wav", "mp3"],
            key=f"upload_audio_{st.session_state.upload_counter}"
        )
        if uploaded_file is not None:
            # Load environment variables
            load_dotenv()
            # Read the uploaded file
            audio_data = uploaded_file.read()

            # Define the S3 key (path) where the file will be stored
            # Ensure the file extension matches the uploaded file type
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if file_extension == 'mp3':
                s3_key = f"{folder_name}/audio.mp3"
                content_type = 'audio/mpeg'
            else:
                s3_key = f"{folder_name}/audio.wav"
                content_type = 'audio/wav'

            # Upload the file to S3
            try:
                with st.spinner('מעלה את הקובץ ל-S3...'):
                    s3_client = boto3.client('s3', region_name='us-east-1')
                    s3_client.put_object(
                        Bucket=bucket_name,
                        Key=s3_key,
                        Body=audio_data,
                        ContentType=content_type
                    )
                st.write(f"S3 Path: {s3_key}")
                st.success("הקובץ הועלה בהצלחה.")  # "The file has been uploaded successfully."

                # Initialize the Transcribe client
                transcribe_client = boto3.client('transcribe', region_name='us-east-1')  # Corrected region

                # Generate a unique transcription job name
                transcription_job_name = f"transcription_{uuid.uuid4()}"

                # Define the S3 URI of the uploaded audio file
                media_uri = f"s3://{bucket_name}/{s3_key}"

                # Start the transcription job
                with st.spinner('מתחיל תמלול הקובץ. נא המתינו...'):
                    transcribe_client.start_transcription_job(
                        TranscriptionJobName=transcription_job_name,
                        Media={'MediaFileUri': media_uri},
                        MediaFormat=file_extension,  # 'wav' or 'mp3'
                        LanguageCode='he-IL',  # Hebrew language code
                        Settings={
                            'ShowSpeakerLabels': True,  # Enable speaker identification
                            'MaxSpeakerLabels': 2  # Adjust the number of speakers as needed
                        }
                    )

                # Polling the transcription job status
                with st.spinner('מתחיל תמלול הקובץ. נא המתינו...'):
                    start_time = time.time()
                    timeout = 600  # 10 minutes
                    while True:
                        status = transcribe_client.get_transcription_job(TranscriptionJobName=transcription_job_name)
                        job_status = status['TranscriptionJob']['TranscriptionJobStatus']
                        if job_status in ['COMPLETED', 'FAILED']:
                            break
                        if time.time() - start_time > timeout:
                            st.error("הקובץ התמלול חריג זמן המתנה.")  # "Transcription job timed out."
                            return
                        time.sleep(2)  # Wait for 2 seconds before checking the status again

                if job_status == 'COMPLETED':
                    # Retrieve the transcript URI
                    transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']

                    # Fetch the transcription result
                    transcript_response = requests.get(transcript_uri)
                    transcript_json = transcript_response.json()
                    transcription_text = transcript_json['results']['transcripts'][0]['transcript']

                    # Define the S3 key for raw.txt
                    raw_text_key = f"{folder_name}/raw.txt"

                    # Upload the transcription to S3 as raw.txt
                    with st.spinner('מעלה את התמלול הגולמי ל-S3...'):
                        s3_client.put_object(
                            Bucket=bucket_name,
                            Key=raw_text_key,
                            Body=transcription_text,
                            ContentType='text/plain'
                        )
                    st.success(f"הקובץ תומלל בהצלחה ונשמר כאן: {raw_text_key}")  # "The file was transcribed successfully."

                    ################ Start clean text process
                    # **Use the transcription_text directly instead of fetching from S3**
                    with st.spinner('מנקה את התמלול...'):
                        clean_text = ai_agent_clean(transcription_text)
                        s3_clean = f"{folder_name}/clean.txt"
                        s3_client.put_object(
                            Bucket=bucket_name,
                            Key=s3_clean,
                            Body=clean_text,
                            ContentType='text/plain'
                        )
                    st.success(f"הקובץ המתומלל נוקה ונשמר כאן: {s3_clean}")  # "The file was cleaned successfully."

                    ################ Start summarize text process
                    with st.spinner('סוכם את התמלול...'):
                        summary_text = ai_agent_summary(clean_text)
                        s3_summary = f"{folder_name}/summary.txt"
                        s3_client.put_object(
                            Bucket=bucket_name,
                            Key=s3_summary,
                            Body=summary_text,
                            ContentType='text/plain'
                        )
                    st.success(f"הסיכום נשמר כאן: {s3_summary}")  # "The summary was saved successfully."

                    # Show buttons after processing
                    st.session_state.show_buttons = True
                    st.session_state.upload_counter += 1  # Increment the counter to reset uploader

                    # Optionally, uncheck the checkbox after upload
                    # st.session_state.toggle_upload = False

                else:
                    st.error("התרגום נכשל. נסה שנית.")  # "Transcription failed. Please try again."

            except Exception as e:
                st.error(f"העלאת הקובץ נכשלה: {e}")  # "File upload failed: {error}"
