import os
import subprocess
import gradio as gr
import pysrt
import google.generativeai as genai
from google.colab import files
import edge_tts
import asyncio
from pydub import AudioSegment

# تنظیمات زبان‌ها
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

# تنظیمات صداها
VOICE_MAP = {
    "فرید (FA)": "fa-IR-FaridNeural",
    "آرزو (FA)": "fa-IR-ArezooNeural",
    "DilaraNeutral (TR)": "tr-TR-DilaraNeural",
    "AhmetNeutral (TR)": "tr-TR-AhmetNeural"
}

def cleanup_files():
    """پاکسازی فایل‌های موقت"""
    files_to_remove = ['audio.wav', 'audio.srt', 'audio_fa.srt', 'final_video.mp4']
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
    return "Files cleaned up successfully!"

def process_video(video_file, youtube_url):
    """پردازش ویدیو آپلودی یا یوتیوب"""
    cleanup_files()
    
    if youtube_url:
        try:
            subprocess.run(['yt-dlp', '-f', 'best', '-o', 'video.mp4', youtube_url])
            subprocess.run(['ffmpeg', '-i', 'video.mp4', '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', 'audio.wav'])
            return "YouTube video processed successfully!"
        except Exception as e:
            return f"Error processing YouTube video: {str(e)}"
    
    elif video_file is not None:
        try:
            subprocess.run(['ffmpeg', '-i', video_file.name, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', 'audio.wav'])
            return "Video file processed successfully!"
        except Exception as e:
            return f"Error processing video file: {str(e)}"
    
    return "Please provide a video file or YouTube URL."

def extract_text(extraction_method, subtitle_file):
    """استخراج متن از صدا یا آپلود زیرنویس"""
    if extraction_method == "Whisper" and os.path.exists('audio.wav'):
        subprocess.run(['whisper', 'audio.wav', '--model', 'large', '--output_dir', './', '--output_format', 'srt'])
        return "Text extracted using Whisper."
    
    elif extraction_method == "Upload Subtitle" and subtitle_file is not None:
        try:
            # خواندن محتوای فایل آپلود شده
            content = subtitle_file.name
            # ذخیره با نام audio.srt
            with open('audio.srt', 'w', encoding='utf-8') as f:
                f.write(content)
            return "Subtitle file uploaded and saved as audio.srt successfully!"
        except Exception as e:
            return f"Error processing subtitle file: {str(e)}"
    
    return "Please extract text using Whisper or upload a subtitle file."


def translate_subtitle(text, api_key, source_lang, target_lang):
    """ترجمه متن با API گوگل"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"Translate this text from {source_lang} to {target_lang}: {text}"
    response = model.generate_content(prompt)
    return response.text

def process_translation(translation_method, api_key, source_lang, target_lang, custom_subtitle):
    """پردازش ترجمه با هوش مصنوعی یا آپلود ترجمه"""
    if translation_method == "AI Translation":
        if not api_key:
            return "Please provide a valid API key."
        
        try:
            if not os.path.exists('audio.srt'):
                return "Please extract or upload source subtitle first!"
                
            subs = pysrt.open('audio.srt')
            for sub in subs:
                sub.text = translate_subtitle(sub.text, api_key, source_lang, target_lang)
            subs.save('audio_fa.srt', encoding='utf-8')
            return f"Translation from {source_lang} to {target_lang} completed!"
        except Exception as e:
            return f"Error: {str(e)}"
    
    elif translation_method == "Upload Translation" and custom_subtitle is not None:
        try:
            # خواندن محتوای فایل ترجمه آپلود شده
            content = custom_subtitle.name
            # ذخیره با نام audio_fa.srt
            with open('audio_fa.srt', 'w', encoding='utf-8') as f:
                f.write(content)
            return "Translated subtitle uploaded and saved as audio_fa.srt successfully!"
        except Exception as e:
            return f"Error processing translated subtitle: {str(e)}"
    
    return "Please choose a translation method."

async def generate_speech_segment(text, voice, output_file):
    """تولید گفتار برای هر سگمنت"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def handle_generate_speech(voice_choice):
    """مدیریت تولید گفتار"""
    try:
        voice = VOICE_MAP[voice_choice]
        subs = pysrt.open('audio_fa.srt')
        
        for i, sub in enumerate(subs):
            asyncio.run(generate_speech_segment(sub.text, voice, f'segment_{i}.mp3'))
        
        return "Speech segments generated successfully!"
    except Exception as e:
        return f"Error generating speech: {str(e)}"

def create_final_video(voice_choice, keep_original, original_volume):
    """ساخت ویدیوی نهایی"""
    try:
        # ترکیب صدا و ویدیو
        subprocess.run(['ffmpeg', '-i', 'video.mp4', '-i', 'final_audio.wav', 
                       '-c:v', 'copy', '-c:a', 'aac', 'final_video.mp4'])
        
        return gr.Video.update(value='final_video.mp4'), "Final video created successfully!"
    except Exception as e:
        return None, f"Error creating final video: {str(e)}"

# رابط کاربری
with gr.Blocks(title="Video Dubbing Tool", theme=gr.themes.Base()) as app:
    gr.Markdown("# Video Dubbing Tool")
    gr.HTML(
        """
        <div style="text-align: center; margin-bottom: 1rem">
            <a href="https://youtube.com/@aigolden" target="_blank">
                <button style="padding: 0.5rem 1rem; margin: 0 0.5rem; border-radius: 0.5rem; background-color: #FF0000; color: white; border: none; cursor: pointer;">
                    YouTube: @aigolden
                </button>
            </a>
            <a href="https://t.me/ai_golden" target="_blank">
                <button style="padding: 0.5rem 1rem; margin: 0 0.5rem; border-radius: 0.5rem; background-color: #0088cc; color: white; border: none; cursor: pointer;">
                    Telegram: @ai_golden
                </button>
            </a>
        </div>
        """
    )
    
    with gr.Tab("1. Upload Video"):
        gr.Markdown("### Upload your video or provide a YouTube URL")
        with gr.Row():
            video_file = gr.File(label="Upload Video File", file_types=["video"])
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
        
        extract_btn.click(extract_text, inputs=[extraction_method, subtitle_file], outputs=extract_status)
    
    with gr.Tab("3. Translate Subtitles"):
        gr.Markdown("### Translate subtitles using AI or upload translated subtitle")
        translation_method = gr.Radio(["AI Translation", "Upload Translation"], label="Translation Method", value="AI Translation")
        
        with gr.Group(visible=True) as ai_translation_group:
            api_key = gr.Textbox(label="Google API Key", type="password")
            source_lang = gr.Dropdown(list(LANGUAGE_MAP.keys()), label="Source Language", value="English (EN)")
            target_lang = gr.Dropdown(list(LANGUAGE_MAP.keys()), label="Target Language", value="Persian (FA)")
        
        custom_subtitle = gr.File(label="Upload Translated SRT File", file_types=[".srt", ".txt", ".vtt"], file_count="single")
        translate_btn = gr.Button("Translate Subtitles")
        translate_status = gr.Textbox(label="Status")
        
        translate_btn.click(process_translation, inputs=[translation_method, api_key, source_lang, target_lang, custom_subtitle], outputs=translate_status)
    
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
        
        create_btn.click(create_final_video, inputs=[final_voice_choice, keep_original, original_volume], outputs=[final_video, final_status])
    
    with gr.Tab("Cleanup"):
        gr.Markdown("### Clean up files from previous sessions")
        cleanup_btn = gr.Button("Clean Up Files")
        cleanup_status = gr.Textbox(label="Status")
        
        cleanup_btn.click(cleanup_files, inputs=[], outputs=cleanup_status)

if __name__ == "__main__":
    app.launch(share=True)
