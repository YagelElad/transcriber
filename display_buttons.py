# display_buttons.py

import streamlit as st
import boto3

def handle_display_buttons(folder_name, bucket_name):
    """
    Handles the display of the three buttons that show different transcription texts
    and allows updating the visit summary.
    """
    if st.session_state.show_buttons:
        col1, col2, col3 = st.columns(3)

        # Flags to determine which text box to display
        show_raw_text = False
        show_clean_text = False
        show_summary_text = False

        # Button to display original transcription
        with col3:
            if st.button("תמלול מקורי"):
                s3_raw_text_path = f"{folder_name}/raw.txt"
                try:
                    with st.spinner('מעלה את התמלול המקורי...'):
                        s3_client = boto3.client('s3', region_name='us-east-1')
                        response = s3_client.get_object(Bucket=bucket_name, Key=s3_raw_text_path)
                        raw_text_content = response['Body'].read().decode('utf-8')
                        st.session_state.raw_text_content = raw_text_content  # Store in session
                        show_raw_text = True
                        st.session_state.show_update_summary = False  # Hide the Update Summary button
                except Exception as e:
                    st.error(f"אינו מצליח לאחזר את התמלול המקורי: {e}")  # "Could not retrieve original transcription: {error}"

        # Button to display cleaned transcription
        with col2:
            if st.button("תמלול מתוקן"):
                s3_clean_text_path = f"{folder_name}/clean.txt"
                try:
                    with st.spinner('מעלה את התמלול המתוקן...'):
                        s3_client = boto3.client('s3', region_name='us-east-1')
                        response = s3_client.get_object(Bucket=bucket_name, Key=s3_clean_text_path)
                        clean_text_content = response['Body'].read().decode('utf-8')
                        st.session_state.clean_text_content = clean_text_content  # Store in session
                        show_clean_text = True
                        st.session_state.show_update_summary = False  # Hide the Update Summary button
                except Exception as e:
                    st.error(f"אינו מצליח לאחזר את התמלול המתוקן: {e}")  # "Could not retrieve cleaned transcription: {error}"

        # Button to display visit summary
        with col1:
            if st.button("סיכום הביקור"):
                s3_summary_text_path = f"{folder_name}/summary.txt"
                try:
                    with st.spinner('מעלה את סיכום הביקור...'):
                        s3_client = boto3.client('s3', region_name='us-east-1')
                        response = s3_client.get_object(Bucket=bucket_name, Key=s3_summary_text_path)
                        summary_text_content = response['Body'].read().decode('utf-8')
                        st.session_state.summary_text_content = summary_text_content  # Store in session
                        show_summary_text = True
                        st.session_state.show_update_summary = True
                except Exception as e:
                    st.error(f"אינו מצליח לאחזר את סיכום הביקור: {e}")  # "Could not retrieve visit summary: {error}"

        # Display the appropriate text box in full width
        st.markdown("---")  # Add a separator for clarity
        if show_raw_text:
            st.text_area(
                "טקסט מקורי",
                value=st.session_state.raw_text_content,
                height=200,
                key="raw_text_display",
                disabled=True
            )
        elif show_clean_text:
            st.text_area(
                "טקסט מתוקן",
                value=st.session_state.clean_text_content,
                height=200,
                key="clean_text_display",
                disabled=True
            )
        elif show_summary_text:
            st.text_area(
                "סיכום הביקור",
                value=st.session_state.summary_text_content,
                height=200,
                key="summary_text_display",
                disabled=True  # Make it editable if needed
            )

        # Display the Update Summary button below the summary text_area
        if st.session_state.get('show_update_summary', False):
            st.markdown("---")  # Separator for clarity
            updated_summary = st.text_area(
                "סיכום הביקור",
                value=st.session_state.get('summary_text_content', ''),
                height=200,
                key="summary_text_editable",
                disabled=False  # Allow editing
            )

            if st.button("עדכן סיכום"):
                try:
                    # Get the updated summary from the editable text area
                    new_summary = st.session_state.summary_text_editable

                    # Upload the updated summary back to S3
                    s3_summary_text_path = f"{folder_name}/summary.txt"
                    with st.spinner('מעלה את סיכום הביקור החדש...'):
                        s3_client = boto3.client('s3', region_name='us-east-1')
                        s3_client.put_object(
                            Bucket=bucket_name,
                            Key=s3_summary_text_path,
                            Body=new_summary,
                            ContentType='text/plain'
                        )
                    st.success("הסיכום עודכן בהצלחה.")  # "The summary was updated successfully."

                    # Update the session state with the new summary
                    st.session_state.summary_text_content = new_summary

                    # Optionally, reset the flag to hide the Update Summary button
                    st.session_state.show_update_summary = False
                except Exception as e:
                    st.error(f"עדכון הסיכום נכשל: {e}")  # "Updating summary failed: {error}"
