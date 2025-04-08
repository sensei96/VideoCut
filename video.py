import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import shutil  
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from tqdm import tqdm

def log_message(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def detect_nvidia_gpu():
    """Cek apakah sistem memiliki GPU NVIDIA dengan nvidia-smi."""
    return shutil.which("nvidia-smi") is not None

VIDEO_CODEC = "h264_nvenc" if detect_nvidia_gpu() else "libx264"

def detect_scenes(video_path):
    log_message(f"Membuka video: {video_path}")
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=30.0))
    log_message("Mendeteksi scene...")
    scene_manager.detect_scenes(video, show_progress=True)
    scene_list = scene_manager.get_scene_list()
    
    log_message(f"Ditemukan {len(scene_list)} scene.")
    return [(start.get_seconds(), end.get_seconds()) for start, end in scene_list]

def cut_video(video_path, output_dir, start_time, end_time, use_scene_detection):
    os.makedirs(output_dir, exist_ok=True)

    if use_scene_detection:
        scenes = detect_scenes(video_path)
        if not scenes:
            messagebox.showinfo("Info", "Tidak ada adegan yang terdeteksi!")
            return

        for i, (start, end) in enumerate(scenes):
            output_path = os.path.join(output_dir, f"scene_{i+1}.mp4")
            process_ffmpeg(video_path, start, end, output_path)

        log_message(f"Pemotongan selesai! {len(scenes)} adegan disimpan di {output_dir}")
    else:
        if start_time >= end_time:
            messagebox.showerror("Error", "Waktu mulai harus lebih kecil dari waktu akhir!")
            return
        
        output_path = os.path.join(output_dir, "cropped_video.mp4")
        process_ffmpeg(video_path, start_time, end_time, output_path)
    
    messagebox.showinfo("Selesai", "Proses pemotongan selesai!")

def process_ffmpeg(video_path, start, end, output_path):
    log_message(f"Memotong: {start:.2f}s - {end:.2f}s -> {output_path}")
    log_message(f"Codec yang digunakan: {VIDEO_CODEC}")

    cmd = [
        "ffmpeg", "-y", "-i", video_path, "-ss", str(start), "-to", str(end),
        "-c:v", VIDEO_CODEC, "-preset", "slow", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        output_path
    ]
  


    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
            log_message(f"SUCCESS: Video berhasil disimpan: {output_path}")
        else:
            log_message(f"WARNING: Gagal menyimpan video: {output_path}")
            os.remove(output_path)
    except Exception as e:
        log_message(f"ERROR: Gagal memotong video: {e}")

# GUI Tkinter
root = tk.Tk()
root.title("Video Cutter & Scene Detector")
root.geometry("500x400")

entry_var = tk.StringVar()
output_var = tk.StringVar()
start_var = tk.DoubleVar(value=0.0)
end_var = tk.DoubleVar(value=0.0)
scene_detection_var = tk.BooleanVar(value=False)  # Pilihan checkbox untuk deteksi scene

def select_video():
    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mkv")])
    if file_path:
        entry_var.set(file_path)

def select_output_dir():
    directory = filedialog.askdirectory()
    if directory:
        output_var.set(directory)

def toggle_scene_detection():
    """Mengaktifkan atau menonaktifkan input start/end berdasarkan checkbox scene detection"""
    if scene_detection_var.get():
        start_entry.config(state=tk.DISABLED)
        end_entry.config(state=tk.DISABLED)
    else:
        start_entry.config(state=tk.NORMAL)
        end_entry.config(state=tk.NORMAL)

def process_video():
    video_path = entry_var.get()
    output_dir = output_var.get()
    start_time = start_var.get()
    end_time = end_var.get()
    use_scene_detection = scene_detection_var.get()
    
    if not os.path.exists(video_path):
        messagebox.showerror("Error", "Pilih file video terlebih dahulu!")
        return
    if not output_dir:
        messagebox.showerror("Error", "Pilih folder untuk menyimpan hasil!")
        return
    
    cut_video(video_path, output_dir, start_time, end_time, use_scene_detection)

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(pady=20)

tk.Label(frame, text="Pilih Video:").pack()
tk.Entry(frame, textvariable=entry_var, width=50).pack()
tk.Button(frame, text="Browse", command=select_video).pack(pady=5)

tk.Label(frame, text="Pilih Folder Output:").pack()
tk.Entry(frame, textvariable=output_var, width=50).pack()
tk.Button(frame, text="Browse Folder", command=select_output_dir).pack(pady=5)

# Checkbox untuk memilih mode pemotongan
scene_check = tk.Checkbutton(frame, text="Gunakan Deteksi Scene", variable=scene_detection_var, command=toggle_scene_detection)
scene_check.pack(pady=5)

# Input waktu mulai dan akhir (dinonaktifkan jika pakai scene detection)
tk.Label(frame, text="Waktu Mulai (detik):").pack()
start_entry = tk.Entry(frame, textvariable=start_var, width=10)
start_entry.pack()

tk.Label(frame, text="Waktu Akhir (detik):").pack()
end_entry = tk.Entry(frame, textvariable=end_var, width=10)
end_entry.pack()

tk.Button(frame, text="Proses Video", command=process_video).pack(pady=10)

root.mainloop()
