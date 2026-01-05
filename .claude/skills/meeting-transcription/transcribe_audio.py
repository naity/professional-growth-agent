#!/usr/bin/env python3
"""
AWS Transcribe Integration Script
Uploads audio to S3, starts transcription, and returns the transcript.
"""

import boto3
import time
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
S3_BUCKET = os.environ.get('MEETING_TRANSCRIBE_S3_BUCKET', 'meeting-coach-transcriptions')
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
CLEANUP_AUDIO = os.environ.get('CLEANUP_AUDIO_FROM_S3', 'true').lower() == 'true'


def get_file_format(file_path):
    """Determine the audio format from file extension."""
    ext = Path(file_path).suffix.lower().lstrip('.')
    
    format_mapping = {
        'mp3': 'mp3',
        'mp4': 'mp4',
        'wav': 'wav',
        'flac': 'flac',
        'm4a': 'mp4',
        'ogg': 'ogg',
        'webm': 'webm',
        'amr': 'amr'
    }
    
    return format_mapping.get(ext, 'mp3')


def upload_to_s3(file_path, s3_client):
    """Upload audio file to S3 bucket."""
    file_name = Path(file_path).name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    s3_key = f"uploads/{timestamp}_{file_name}"
    
    try:
        print(f"Uploading {file_path} to S3 bucket {S3_BUCKET}...")
        s3_client.upload_file(file_path, S3_BUCKET, s3_key)
        print(f"✓ Uploaded to s3://{S3_BUCKET}/{s3_key}")
        return s3_key
    except Exception as e:
        print(f"Error uploading to S3: {e}", file=sys.stderr)
        raise


def start_transcription_job(s3_key, audio_format, transcribe_client, language_code='en-US'):
    """Start an AWS Transcribe job with speaker labels.
    
    Args:
        s3_key: S3 object key for the audio file
        audio_format: Audio format (mp3, wav, etc.)
        transcribe_client: Boto3 Transcribe client
        language_code: Language code (en-US, zh-CN, zh-TW, es-ES, fr-FR, de-DE, ja-JP, ko-KR)
    
    Always uses speaker labels to identify different speakers in the conversation.
    """
    job_name = f"meeting-transcription-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    job_uri = f"s3://{S3_BUCKET}/{s3_key}"
    
    try:
        print(f"Starting transcription job: {job_name}...")
        print(f"Using language: {language_code} (speaker labels enabled)...")
        
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': job_uri},
            MediaFormat=audio_format,
            LanguageCode=language_code,
            Settings={
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': 10
            }
        )
        
        print(f"✓ Transcription job started: {job_name}")
        return job_name
    except Exception as e:
        print(f"Error starting transcription: {e}", file=sys.stderr)
        raise


def wait_for_transcription(job_name, transcribe_client):
    """Poll transcription job until complete."""
    print("Waiting for transcription to complete...")
    
    max_wait_time = 600  # 10 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        response = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name
        )
        
        status = response['TranscriptionJob']['TranscriptionJobStatus']
        
        if status == 'COMPLETED':
            print("✓ Transcription completed!")
            return response['TranscriptionJob']['Transcript']['TranscriptFileUri']
        elif status == 'FAILED':
            failure_reason = response['TranscriptionJob'].get('FailureReason', 'Unknown')
            raise Exception(f"Transcription failed: {failure_reason}")
        
        print(f"Status: {status}... (waiting)")
        time.sleep(5)
    
    raise Exception("Transcription timeout - job took too long")


def get_transcript_text(transcript_uri):
    """Download and parse the transcript JSON."""
    import urllib.request
    
    try:
        print(f"Downloading transcript from {transcript_uri}...")
        with urllib.request.urlopen(transcript_uri) as response:
            transcript_data = json.loads(response.read().decode())
        
        # Extract the transcript text
        transcript_text = transcript_data['results']['transcripts'][0]['transcript']
        
        # Extract speaker labels if available (will be empty with auto language detection)
        items = transcript_data['results'].get('items', [])
        speaker_segments = []
        current_speaker = None
        current_text = []
        
        for item in items:
            if 'speaker_label' in item:
                speaker = item['speaker_label']
                if speaker != current_speaker:
                    if current_speaker and current_text:
                        speaker_segments.append(f"{current_speaker}: {' '.join(current_text)}")
                    current_speaker = speaker
                    current_text = []
            
            if item['type'] == 'pronunciation':
                current_text.append(item['alternatives'][0]['content'])
            elif item['type'] == 'punctuation':
                if current_text:
                    current_text[-1] += item['alternatives'][0]['content']
        
        # Add the last segment
        if current_speaker and current_text:
            speaker_segments.append(f"{current_speaker}: {' '.join(current_text)}")
        
        return transcript_text, speaker_segments
    except Exception as e:
        print(f"Error downloading transcript: {e}", file=sys.stderr)
        raise


def cleanup(s3_key, job_name, s3_client, transcribe_client):
    """Clean up S3 files and transcription job."""
    if CLEANUP_AUDIO:
        try:
            print("Cleaning up...")
            s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
            print(f"✓ Deleted s3://{S3_BUCKET}/{s3_key}")
        except Exception as e:
            print(f"Warning: Could not delete S3 file: {e}", file=sys.stderr)
    
    # Note: Transcription jobs are retained for 90 days by default
    # You can delete them manually if needed


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Transcribe audio files using AWS Transcribe')
    parser.add_argument('audio_file', help='Path to the audio file')
    parser.add_argument('--language', 
                       default='en-US',
                       help='Language code (en-US, zh-CN, zh-TW, es-ES, fr-FR, de-DE, ja-JP, ko-KR)')
    
    args = parser.parse_args()
    audio_file_path = args.audio_file
    language_code = args.language
    
    # Validate file exists
    if not os.path.exists(audio_file_path):
        print(f"Error: File not found: {audio_file_path}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize AWS clients
    try:
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        transcribe_client = boto3.client('transcribe', region_name=AWS_REGION)
    except Exception as e:
        print(f"Error initializing AWS clients: {e}", file=sys.stderr)
        print("Make sure AWS credentials are configured properly.", file=sys.stderr)
        sys.exit(1)
    
    s3_key = None
    job_name = None
    
    try:
        # Step 1: Upload to S3
        audio_format = get_file_format(audio_file_path)
        s3_key = upload_to_s3(audio_file_path, s3_client)
        
        # Step 2: Start transcription
        job_name = start_transcription_job(s3_key, audio_format, transcribe_client, language_code)
        
        # Step 3: Wait for completion
        transcript_uri = wait_for_transcription(job_name, transcribe_client)
        
        # Step 4: Get transcript text
        transcript_text, speaker_segments = get_transcript_text(transcript_uri)
        
        # Step 5: Output results
        print("\n" + "="*80)
        print("TRANSCRIPT")
        print("="*80)
        print("\n--- Full Transcript ---")
        print(transcript_text)
        
        if speaker_segments:
            print("\n--- Speaker-Segmented Transcript ---")
            for segment in speaker_segments:
                print(segment)
        
        print("\n" + "="*80)
        
        # Step 6: Cleanup
        cleanup(s3_key, job_name, s3_client, transcribe_client)
        
    except Exception as e:
        print(f"\nTranscription failed: {e}", file=sys.stderr)
        
        # Attempt cleanup even on failure
        if s3_key and job_name:
            try:
                cleanup(s3_key, job_name, s3_client, transcribe_client)
            except:
                pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()

