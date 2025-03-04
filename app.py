import os
import base64
import subprocess
import asyncio
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai
import gradio as gr
import edge_tts
import yt_dlp
import pysrt
from pydub import AudioSegment

# Install required packages (uncomment when running in Colab)
# !pip install git+$(base64.b64decode("aHR0cHM6Ly9naXRodWIuY29tL3lhcmFuYmFyemkvYWlnb2xkZW4tYXVkaW8tdG8tdGV4dC5naXQ=").decode())
# !pip install edge_tts yt-dlp pysrt rubberband-cli pydub gradio
# !apt-get update && apt-get install -y ffmpeg rubberband-cli

# Define voice options
VOICE_MAP = {
    # Persian
    "فرید (FA)": "fa-IR-FaridNeural",
    "دلارا (FA)": "fa-IR-DilaraNeural",
    # English
    "Jenny (EN)": "en-US-JennyNeural",
    "Guy (EN)": "en-US-GuyNeural",
    # German
    "Katja (DE)": "de-DE-KatjaNeural",
    "Conrad (DE)": "de-DE-ConradNeural",
    # French
    "Denise (FR)": "fr-FR-DeniseNeural",
    "Henri (FR)": "fr-FR-HenriNeural",
    # Italian
    "Isabella (IT)": "it-IT-IsabellaNeural",
    "Diego (IT)": "it-IT-DiegoNeural",
    # Spanish
    "Elvira (ES)": "es-ES-ElviraNeural",
    "Alvaro (ES)": "es-ES-AlvaroNeural",
    # Chinese
    "Xiaoxiao (ZH)": "zh-CN-XiaoxiaoNeural",
    "Yunyang (ZH)": "zh-CN-YunyangNeural",
    # Korean
    "SunHi (KO)": "ko-KR-SunHiNeural",
    "InJoon (KO)": "ko-KR-InJoonNeural",
    # Russian
    "Svetlana (RU)": "ru-RU-SvetlanaNeural",
    "Dmitry (RU)": "ru-RU-DmitryNeural",
    # Arabic
    "Amina (AR)": "ar-EG-AminaNeural",
    "Hamed (AR)": "ar-EG-HamedNeural",
    # Japanese
    "Nanami (JA)": "ja-JP-NanamiNeural",
    "Keita (JA)": "ja-JP-KeitaNeural"
}

# Language mapping for translation
LANGUAGE_MAP = {
    "Persian (FA)": "فارسی",
    "English (EN)": "English",
    "German (DE)": "German",
    "French (FR)": "French",
    "Italian (IT)": "Italian",
    "Spanish (ES)": "Spanish",
    "Chinese (ZH)": "Chinese",
    "Korean (KO)": "Korean",
    "Russian (RU)": "Russian",
    "Arabic (AR)": "Arabic",
    "Japanese (JA)": "Japanese"
}
# Function to clean up previous files
def cleanup_files():
    files_to_remove = ['input_video.mp4', 'audio.wav', 'audio.srt', 'audio_fa.srt', 'audio_translated.srt']
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
    
    if os.path.exists('dubbing_project'):
        import shutil
        shutil.rmtree('dubbing_project')
    
    os.makedirs('dubbing_project/dubbed_segments', exist_ok=True)
    return "Clean up completed."

# Function to handle video upload
def process_video(video_file, youtube_url):
    cleanup_files()
    
    if video_file is not None:
        # Process uploaded video
        with open('input_video.mp4', 'wb') as f:
            f.write(video_file)
        subprocess.run(['ffmpeg', '-i', 'input_video.mp4', '-vn', 'audio.wav'])
        return "Video uploaded and audio extracted successfully."
    
    elif youtube_url:
        # Process YouTube video
        video_opts = {
            'format': 'best',
            'outtmpl': 'input_video.mp4'
        }
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            ydl.download([youtube_url])
        
        audio_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'outtmpl': 'audio'
        }
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.download([youtube_url])
        
        return "YouTube video downloaded and processed successfully."
    
    else:
        return "Please upload a video file or provide a YouTube URL."

# Function to extract text from audio
def extract_text(extraction_method, subtitle_file):
    if extraction_method == "Whisper" and os.path.exists('audio.wav'):
        subprocess.run(['whisper', 'audio.wav', '--model', 'large', '--output_dir', './', '--output_format', 'srt'])
        return "Text extracted using Whisper."
    
    elif extraction_method == "Upload Subtitle" and subtitle_file is not None:
        uploaded = files.upload()
        subtitle_file = next(iter(uploaded.keys()))
        os.rename(subtitle_file, 'audio.srt')
        return "Subtitle file uploaded successfully."
    
    else:
        return "Please extract text using Whisper or upload a subtitle file."

# Function to translate subtitles
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def translate_subtitle(text, api_key, source_lang, target_lang):
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel('gemini-1.5-flash', safety_settings={
        genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
    })
    
    target_lang_name = LANGUAGE_MAP.get(target_lang, "English")
    
    if target_lang == "Persian (FA)":
        prompt = f"""دستورالعمل:
        1. فقط متن را به فارسی عامیانه و لحن خودمونی ترجمه کن
        2. هرجا لازمه از نقطه و کاما و علائم نگارشی استفاده کن
        3. اضافه گویی در ترجمه ممنوع
        متن برای ترجمه:
        {text}"""
    else:
        prompt = f"""Instruction:
        1. Please translate the text to {target_lang_name} with the same tone
        2. Use appropriate punctuation where necessary
        3. No additional explanation or text
        Text to translate:
        {text}"""
    
    response = model.generate_content(prompt)
    time.sleep(3)
    return response.text

# Function to process all translations
def process_translation(translation_method, api_key, source_lang, target_lang, custom_subtitle):
    if translation_method == "AI Translation":
        if not api_key:
            return "Please provide a valid API key."
        
        try:
            subs = pysrt.open('audio.srt')
            for i, sub in enumerate(subs):
                sub.text = translate_subtitle(sub.text, api_key, source_lang, target_lang)
            
            subs.save('audio_translated.srt', encoding='utf-8')
            os.rename('audio_translated.srt', 'audio_fa.srt')
            return f"Translation from {source_lang} to {target_lang} completed successfully."
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    elif translation_method == "Upload Translation" and custom_subtitle is not None:
        from google.colab import files
        uploaded = files.upload()
        subtitle_file = next(iter(uploaded.keys()))
        os.rename(subtitle_file, 'audio_fa.srt')
        return "Translated subtitle file uploaded successfully."
    
    else:
        return "Please choose a translation method and provide required information."

# Function to generate speech segments asynchronously
async def generate_speech_segments(voice_choice):
    subs = pysrt.open('audio_fa.srt')
    
    selected_voice = VOICE_MAP.get(voice_choice)
    if not selected_voice:
        return f"Selected voice '{voice_choice}' is not available. Please choose a valid voice."
    
    for i, sub in enumerate(subs):
        # Calculate exact duration
        start_time = sub.start.seconds + sub.start.milliseconds/1000
        end_time = sub.end.seconds + sub.end.milliseconds/1000
        target_duration = end_time - start_time
        
        # Generate speech with Edge TTS
        communicate = edge_tts.Communicate(sub.text, selected_voice)
        await communicate.save(f"dubbing_project/dubbed_segments/temp_{i+1}.mp3")
        
        # Convert to WAV format
        subprocess.run([
            'ffmpeg', '-i', f"dubbing_project/dubbed_segments/temp_{i+1}.mp3",
            '-y', f"dubbing_project/dubbed_segments/temp_wav_{i+1}.wav"
        ])
        
        # Calculate original speech duration
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            f"dubbing_project/dubbed_segments/temp_wav_{i+1}.wav"
        ], capture_output=True, text=True)
        
        original_duration = float(result.stdout.strip())
        
        # Calculate speed factor to match target duration
        speed_factor = original_duration / target_duration
        
        # Adjust duration using rubberband
        subprocess.run([
            'ffmpeg', '-i', f"dubbing_project/dubbed_segments/temp_wav_{i+1}.wav",
            '-filter:a', f'rubberband=tempo={speed_factor}',
            '-y', f"dubbing_project/dubbed_segments/dub_{i+1}.wav"
        ])
        
        # Clean up temporary files
        if os.path.exists(f"dubbing_project/dubbed_segments/temp_{i+1}.mp3"):
            os.remove(f"dubbing_project/dubbed_segments/temp_{i+1}.mp3")
        if os.path.exists(f"dubbing_project/dubbed_segments/temp_wav_{i+1}.wav"):
            os.remove(f"dubbing_project/dubbed_segments/temp_wav_{i+1}.wav")
    
    return f"All speech segments generated successfully with voice {voice_choice}."

# Function to synchronize speech segments
def sync_segments(voice_choice, keep_original, original_volume):
    if not os.path.exists('input_video.mp4'):
        return "Please upload or download a video first."
    
    # Read and process subtitle file
    subs = pysrt.open('audio_fa.srt')
    
    # Set up complex filter for audio mixing
    if keep_original:
        filter_complex = f"[0:a]volume={original_volume}[original_audio];"
    else:
        filter_complex = "[0:a]volume=0[original_audio];"
    
    # Add each segment with precise timing
    valid_segments = []
    for i, sub in enumerate(subs):
        try:
            start_time_ms = (sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds) * 1000 + sub.start.milliseconds
            filter_complex += f"[{i+1}:a]adelay={start_time_ms}|{start_time_ms}[a{i+1}];"
            valid_segments.append(i)
        except Exception as e:
            continue
    
    # Combine valid segments
    merge_command = "[original_audio]"
    for i in valid_segments:
        merge_command += f"[a{i+1}]"
    merge_command += f"amix=inputs={len(valid_segments) + 1}:normalize=0[aout]"
    filter_complex += merge_command
    
    # Build ffmpeg command
    input_files = " ".join([f"-i dubbing_project/dubbed_segments/dub_{i+1}.wav" for i in valid_segments])
    
    # Extract language code for filename
    voice_code = voice_choice.split("(")[1].split(")")[0] if "(" in voice_choice else "FA"
    output_filename = f'final_dubbed_video_{voice_code}.mp4'
    
    # Execute final command
    command = f'ffmpeg -y -i input_video.mp4 {input_files} -filter_complex "{filter_complex}" -map 0:v -map "[aout]" -c:v copy {output_filename}'
    subprocess.run(command, shell=True)
    
    if os.path.exists(output_filename):
        return output_filename
    else:
        return "Error creating final video."

# Function to handle generate speech segments button
def handle_generate_speech(voice_choice):
    return asyncio.run(generate_speech_segments(voice_choice))

# Function to handle final video creation
def create_final_video(voice_choice, keep_original, original_volume):
    result = sync_segments(voice_choice, keep_original, original_volume)
    if result.endswith('.mp4'):
        return result, f"Final video created successfully with {voice_choice} voice."
    else:
        return None, result

# Gradio Interface
with gr.Blocks(title="Video Dubbing Tool", theme=gr.themes.Base()) as app:
    gr.Markdown("# Video Dubbing Tool")
    
    with gr.Tab("1. Upload Video"):
        gr.Markdown("### Upload your video or provide a YouTube URL")
        with gr.Row():
            video_file = gr.File(label="Upload Video File")
            youtube_url = gr.Textbox(label="YouTube URL")
        upload_btn = gr.Button("Process Video")
        upload_status = gr.Textbox(label="Status")
        
        upload_btn.click(process_video, inputs=[video_file, youtube_url], outputs=upload_status)
    
    with gr.Tab("2. Extract Text"):
    gr.Markdown("### Extract text from video audio or upload subtitle")
    extraction_method = gr.Radio(["Whisper", "Upload Subtitle"], label="Extraction Method", value="Whisper")
    subtitle_file = gr.File(label="Upload SRT File", file_types=[".srt", ".txt", ".vtt"], file_count="single")
    extract_btn = gr.Button("Extract Text")
    extract_status = gr.Textbox(label="Status")
    
    with gr.Tab("3. Translate Subtitles"):
    custom_subtitle = gr.File(label="Upload Translated SRT File", file_types=[".srt", ".txt", ".vtt"], file_count="single")
        
        translate_btn.click(
            process_translation, 
            inputs=[translation_method, api_key, source_lang, target_lang, custom_subtitle], 
            outputs=translate_status
        )
    
    with gr.Tab("4. Generate Speech"):
        gr.Markdown("### Generate speech segments with timing")
        voice_choice = gr.Dropdown(list(VOICE_MAP.keys()), label="Voice", value="فرید (FA)")
        generate_btn = gr.Button("Generate Speech Segments")
        generate_status = gr.Textbox(label="Status")
        
        generate_btn.click(handle_generate_speech, inputs=[voice_choice], outputs=generate_status)
    
    with gr.Tab("5. Create Final Video"):
        gr.Markdown("### Combine video with synthesized speech")
        keep_original = gr.Checkbox(label="Keep Original Audio", value=False)
        original_volume = gr.Slider(minimum=0, maximum=1, value=0.05, step=0.005, label="Original Audio Volume")
        final_voice_choice = gr.Dropdown(list(VOICE_MAP.keys()), label="Voice", value="فرید (FA)")
        create_btn = gr.Button("Create Final Video")
        
        with gr.Row():
            final_video = gr.Video(label="Final Video")
            final_status = gr.Textbox(label="Status")
        
        create_btn.click(
            create_final_video, 
            inputs=[final_voice_choice, keep_original, original_volume], 
            outputs=[final_video, final_status]
        )
    
    with gr.Tab("Cleanup"):
        gr.Markdown("### Clean up files from previous sessions")
        cleanup_btn = gr.Button("Clean Up Files")
        cleanup_status = gr.Textbox(label="Status")
        
        cleanup_btn.click(cleanup_files, inputs=[], outputs=cleanup_status)

# Launch app
if __name__ == "__main__":
    app.launch(share=True)
