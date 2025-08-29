import re
import os
import tkinter
import requests
from tqdm import tqdm
import time
import sys
from urllib3.exceptions import IncompleteRead
import tkinter as tk
import tkinter
from tkinter import Tk, Canvas,  Button, PhotoImage, filedialog, ttk,  messagebox
from tkinter import Tk, scrolledtext,  messagebox, ttk, filedialog
import urllib.request
from urllib.parse import urlparse

# Global variables for video quality and season selection (will be initialized after window creation)
selected_quality = None
selected_season = None


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        # For bundled executable
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def download_with_retry(url, save_path, max_retries=3, retry_delay=300):
    for retry in range(max_retries + 1):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an exception if the response status is not 200

            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0
            with open(save_path, "wb") as file, tqdm(
                desc=os.path.basename(url),
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                start_time = time.time()
                for data in response.iter_content(chunk_size=1024):
                    bar.update(len(data))
                    downloaded_size += len(data)
                    file.write(data)
                    update_progress(downloaded_size, total_size)
            return True
        except (IncompleteRead, requests.exceptions.RequestException):
            if retry < max_retries:
                print(
                    f"Retrying download for {url} after {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to download {url} after {max_retries} retries.")
                return False


def update_progress(downloaded_size, total_size):
    progress_value = int((downloaded_size / total_size) * 100)
    progress_bar["value"] = progress_value
    start_time = time.time()
    if progress_value > 0:
        elapsed_time = time.time() - start_time
        remaining_time = (elapsed_time / progress_value) * \
            (100 - progress_value)
        time_remaining.config(
            text=f"Downloading... Estimated time remaining: {format_time(remaining_time)}")
    else:
        time_remaining.config(
            text="Downloading... Estimated time remaining: Calculating...")

    window.update_idletasks()


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_html_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the response status is not 200
        html_content = response.text
        return html_content
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

    # هاي الدالة تابعة الى الترجمة فقط


def download_html_from_url(url, path):
    try:
        response = urllib.request.urlopen(url)
        html_content = response.read().decode("utf-8")

        # Generate a valid file name from the URL
        parsed_url = urlparse(url)
        file_name = parsed_url.netloc + parsed_url.path
        file_name = file_name.replace("/", "_").replace(".", "_")

        # Save the HTML content to a file
        save_path = os.path.join(path, f"{file_name}.html")
        with open(save_path, "w", encoding="utf-8") as file:
            file.write(html_content)

        return html_content
    except Exception as e:
        print("Failed to download HTML content.")
        print(e)
        return None


def start_download_subtitle():
    url = text_widget.get("1.0", tk.END)
    if not url:
        messagebox.showinfo("Info", "Please enter a URL.")
        return

    download_path = filedialog.askdirectory(title="Choose Download Path")
    sample_text = download_html_from_url(path=download_path, url=url)
    sample_text = str(sample_text)
    subtitle_url_pattern = r"https://movie\.vodu\.me/subtitles/(.*?)_S(\d+)E(\d+)_(\d+)\.webvtt\" data-srt=\"(.*?)\.srt"

    subtitle_matches = re.findall(subtitle_url_pattern, sample_text)

    if not download_path:
        messagebox.showinfo("Info", "Download path not selected.")
        return

    os.makedirs(download_path, exist_ok=True)

    text_widget.delete("1.0", tk.END)
    text_widget.insert(tk.END, sample_text)
    text_widget.update_idletasks()
    for series_name, season_number, episode_number, _, subtitle_link in subtitle_matches:
        subtitle_filename = f"{series_name}_S{season_number}E{episode_number}.srt"
        subtitle_save_path = os.path.join(download_path, subtitle_filename)

        progress_bar["value"] = 0
        progress_label.config(text=f"Downloading {subtitle_filename}")

        if not subtitle_link.endswith(".srt"):
            subtitle_link += ".srt"

        if download_with_retry(subtitle_link, subtitle_save_path):
            print("done")
        else:
            print("error")

    progress_bar["value"] = 100
    progress_label.config(text="Download Completed")
    # result_text.insert(tk.END, "Subtitle download completed.\n")


def get_expected_file_size(video_url):
    response = requests.head(video_url)
    content_length_header = response.headers.get('content-length')

    if content_length_header:
        return int(content_length_header)
    else:
        return None


def start_download_video():
    url = text_widget.get("1.0", tk.END).strip()
    if not url:
        messagebox.showinfo("Info", "Please enter a URL.")
        return

    # Get selected quality
    quality = selected_quality.get()
    if not quality:
        messagebox.showinfo(
            "Info", "Please select video quality (360p, 720p, or 1080p).")
        return

    # Get selected season
    season_choice = selected_season.get()
    if not season_choice:
        messagebox.showinfo(
            "Info", "Please select a season option.")
        return

    # Extract the simple text from the URL
    sample_text = get_html_content(url)

    if not sample_text:
        messagebox.showinfo(
            "Info", "Failed to extract simple text from the URL.")
        return

    text_widget.delete("1.0", tk.END)
    text_widget.insert(tk.END, sample_text)
    text_widget.update_idletasks()

    # Create pattern based on selected quality (supports 360p, 720p, 1080p)
    qnum = {
        "360p": "360",
        "720p": "720",
        "1080p": "1080",
    }.get(quality)

    # Primary pattern commonly used on the site
    video_url_pattern = rf"https://\S+-{qnum}\.mp4"
    video_matches = re.findall(video_url_pattern, sample_text)

    # If no matches found for the selected quality, try alternative common patterns
    if not video_matches:
        alternative_patterns = [
            rf"https://\S+-{qnum}p\.mp4",  # e.g., -720p.mp4
            rf"https://\S+_{qnum}\.mp4",   # e.g., _720.mp4
            rf"https://\S+_{qnum}p\.mp4",  # e.g., _720p.mp4
        ]
        for pattern in alternative_patterns:
            video_matches = re.findall(pattern, sample_text)
            if video_matches:
                break

        if not video_matches:
            messagebox.showinfo(
                "Info", f"No {quality} videos found. Try another quality option.")
            return

    # Choose base download path
    base_download_path = filedialog.askdirectory(title="Choose Download Path")

    if not base_download_path:
        messagebox.showinfo("Info", "Download path not selected.")
        return

    # Group videos by season and create folders
    season_videos = {}

    # Extract series name from the first video for folder naming
    series_name = "Unknown_Series"
    if video_matches:
        first_video = os.path.basename(video_matches[0])
        # Extract series name (everything before _S##E##)
        match = re.match(r"(.+?)_S\d+E\d+", first_video)
        if match:
            series_name = match.group(1)

    for video_link in video_matches:
        video_filename = os.path.basename(video_link)

        # Extract season number from filename
        season_match = re.search(r"_S(\d+)E\d+", video_filename)
        if season_match:
            season_num = int(season_match.group(1))

            # Filter based on season selection
            if season_choice != "all" and season_num != int(season_choice):
                continue

            # Group videos by season
            if season_num not in season_videos:
                season_videos[season_num] = []
            season_videos[season_num].append(video_link)

    if not season_videos:
        if season_choice == "all":
            messagebox.showinfo(
                "Info", "No videos found with season information.")
        else:
            messagebox.showinfo(
                "Info", f"No episodes found for Season {season_choice}. Please check if this season exists.")
        return

    total_videos = sum(len(videos) for videos in season_videos.values())
    current_video = 0

    # Download videos grouped by season
    for season_num in sorted(season_videos.keys()):
        videos = season_videos[season_num]

        # Create season folder
        season_folder_name = f"{series_name}_Season_{season_num:02d}"
        season_download_path = os.path.join(
            base_download_path, season_folder_name)
        os.makedirs(season_download_path, exist_ok=True)

        print(f"Created folder: {season_folder_name}")

        for video_link in videos:
            current_video += 1
            video_filename = os.path.basename(video_link)
            video_save_path = os.path.join(
                season_download_path, video_filename)

            if os.path.exists(video_save_path):
                existing_file_size = os.path.getsize(video_save_path)
                expected_file_size = get_expected_file_size(video_link)

                if expected_file_size and existing_file_size == expected_file_size:
                    print(
                        f"File '{video_filename}' already exists and has the correct size. Skipping download.")
                    continue

            progress_bar["value"] = 0
            season_info = f"Season {season_num}" if season_choice != "all" else f"Season {season_num}"
            progress_label.config(
                text=f"Downloading {video_filename} ({quality}) - {season_info} ({current_video}/{total_videos})")

            if download_with_retry(video_link, video_save_path):
                print(
                    f"Downloaded '{video_filename}' to {season_folder_name} in {quality}")
            else:
                print(
                    f"Failed to download '{video_filename}' from {video_link}")

    progress_bar["value"] = 100
    progress_label.config(text="Download Completed")

    # Show completion message with folder info
    completed_seasons = list(season_videos.keys())
    if len(completed_seasons) == 1:
        messagebox.showinfo(
            "Download Complete", f"Downloaded Season {completed_seasons[0]} to folder: {series_name}_Season_{completed_seasons[0]:02d}")
    else:
        season_list = ", ".join([str(s) for s in sorted(completed_seasons)])
        messagebox.showinfo(
            "Download Complete", f"Downloaded Seasons {season_list} to separate folders in:\n{base_download_path}")


def show_developer_info():
    message = "Developer Information:\n\n" \
              "Name: sajjad salam\n" \
              "Email: sajjad.salam.teama@gmail.com\n" \
              "Website: https://engsajjad.000webhostapp.com \n" \
              "GitHub: https://github.com/sajjad-salam\n" \
              "LinkedIn: https://www.linkedin.com/in/sajjad-salam-963043244/ "

    messagebox.showinfo("Developer Information", message)


# def resource_path(relative_path):
#     if hasattr(sys, "_MEIPASS"):
#         # For bundled executable
#         return os.path.join(sys._MEIPASS, relative_path)
#     return os.path.join(os.path.abspath("."), relative_path)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def paste_text():
    text_widget.event_generate("<<Paste>>")


def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)


window = Tk()
window.title("vodu Downloader")
window.geometry("450x750")  # Increased height for season selection
window.configure(bg="#282828")
# window.iconbitmap(icon_path)
window.iconbitmap(default="info")

# Initialize the quality and season selection variables after window creation
selected_quality = tk.StringVar()
selected_season = tk.StringVar()
# Set default quality to 360p and season to all
selected_quality.set("360p")
selected_season.set("all")

canvas = Canvas(
    window,
    bg="#282828",
    height=750,  # Increased height
    width=450,
    bd=0,
    highlightthickness=0,
    relief="ridge"
)

canvas.place(x=0, y=0)


image_path3 = resource_path("gui/assets/button_3.png")
image_image_3 = PhotoImage(file=image_path3)
# About Button
button_3 = Button(
    # name="developer",
    # text="dev.",
    image=image_image_3,
    command=show_developer_info,
    borderwidth=0,
    highlightthickness=0,
    activebackground="#202020",
    cursor="heart",
    relief="flat"
)
button_3.place(
    x=20.0,
    y=21.0,
    width=30.0,
    height=30.0
)

image_path6 = resource_path("gui/assets/logo.png")

image_image_6 = PhotoImage(file=image_path6)
image_6 = canvas.create_image(
    225.0,
    37.0,
    image=image_image_6
)


text_widget = scrolledtext.ScrolledText(
    canvas, width=50, height=0.1, bg="#2D2D2D")
canvas.create_window(224.5, 137.5, window=text_widget)

context_menu = tk.Menu(window, tearoff=0)
context_menu.add_command(label="Paste", command=paste_text)

text_widget.bind("<Button-3>", show_context_menu)

canvas.create_text(
    20.0,
    98.0,
    anchor="nw",
    text=" المسلسل او الفيلم رابط",
    justify="right",
    fill="#FFFFFF",
    font=("Roboto Medium", 14 * -1)
)


# "Include Anonymous Intro" Toggle Button
canvas.create_text(
    75.0,
    178.0,
    anchor="nw",
    text="يجب التأكد جيدا من رابط المسلسل او الفيلم",
    fill="#FFFFFF",
    font=("Roboto Regular", 14 * -1)
)

# Quality selection label
canvas.create_text(
    20.0,
    210.0,
    anchor="nw",
    text="Video Quality / جودة الفيديو:",
    fill="#FFFFFF",
    font=("Roboto Medium", 14 * -1)
)

# Quality selection radio buttons
quality_frame = tk.Frame(canvas, bg="#282828")
canvas.create_window(225.0, 240.0, window=quality_frame)

radio_360p = tk.Radiobutton(
    quality_frame,
    text="360p",
    variable=selected_quality,
    value="360p",
    bg="#282828",
    fg="#FFFFFF",
    selectcolor="#404040",
    activebackground="#282828",
    activeforeground="#FFFFFF",
    font=("Roboto", 12)
)
radio_360p.pack(side="left", padx=10)

radio_720p = tk.Radiobutton(
    quality_frame,
    text="720p",
    variable=selected_quality,
    value="720p",
    bg="#282828",
    fg="#FFFFFF",
    selectcolor="#404040",
    activebackground="#282828",
    activeforeground="#FFFFFF",
    font=("Roboto", 12)
)
radio_720p.pack(side="left", padx=10)

radio_1080p = tk.Radiobutton(
    quality_frame,
    text="1080p",
    variable=selected_quality,
    value="1080p",
    bg="#282828",
    fg="#FFFFFF",
    selectcolor="#404040",
    activebackground="#282828",
    activeforeground="#FFFFFF",
    font=("Roboto", 12)
)
radio_1080p.pack(side="left", padx=10)

# Season selection label
canvas.create_text(
    20.0,
    270.0,
    anchor="nw",
    text="Season Selection / اختيار الموسم:",
    fill="#FFFFFF",
    font=("Roboto Medium", 14 * -1)
)

# Season selection frame
season_frame = tk.Frame(canvas, bg="#282828")
canvas.create_window(225.0, 300.0, window=season_frame)

# Create radio buttons for seasons
radio_all = tk.Radiobutton(
    season_frame,
    text="All Seasons",
    variable=selected_season,
    value="all",
    bg="#282828",
    fg="#FFFFFF",
    selectcolor="#404040",
    activebackground="#282828",
    activeforeground="#FFFFFF",
    font=("Roboto", 10)
)
radio_all.pack(side="left", padx=5)

# Season 1-5 radio buttons
for i in range(1, 6):
    radio_season = tk.Radiobutton(
        season_frame,
        text=f"S{i}",
        variable=selected_season,
        value=str(i),
        bg="#282828",
        fg="#FFFFFF",
        selectcolor="#404040",
        activebackground="#282828",
        activeforeground="#FFFFFF",
        font=("Roboto", 10)
    )
    radio_season.pack(side="left", padx=3)

# Second row for more seasons
season_frame2 = tk.Frame(canvas, bg="#282828")
canvas.create_window(225.0, 330.0, window=season_frame2)

# Season 6-10 radio buttons
for i in range(6, 11):
    radio_season = tk.Radiobutton(
        season_frame2,
        text=f"S{i}",
        variable=selected_season,
        value=str(i),
        bg="#282828",
        fg="#FFFFFF",
        selectcolor="#404040",
        activebackground="#282828",
        activeforeground="#FFFFFF",
        font=("Roboto", 10)
    )
    radio_season.pack(side="left", padx=3)


image_path_subtitle = resource_path("gui/assets/button_subtitle.png")

# Download Subtitle Button
Download_subtitle_button_image = PhotoImage(
    file=image_path_subtitle)

Download_subtitle_button = Button(
    command=start_download_subtitle,
    image=Download_subtitle_button_image,
    borderwidth=0,
    highlightthickness=0,
    activebackground="#202020",
    relief="flat"
)
Download_subtitle_button.place(
    x=18.0,
    y=370.0,  # Moved down to make room for season selection
    width=414.0,
    height=47.0
)

# Simulate existing content height (adjust this value based on your content)
existing_content_height = 200  # Adjusted for new layout

image_path_video = resource_path("gui/assets/button_video.png")

# Download Video Button
Download_video_button_image = PhotoImage(
    file=image_path_video)

Download_video_button = Button(
    command=start_download_video,
    image=Download_video_button_image,
    borderwidth=0,
    highlightthickness=0,
    activebackground="#202020",
    relief="flat"
)

# Calculate y coordinate for the second button
second_button_y = 430  # Fixed position for better layout

Download_video_button.place(
    x=18.0,
    y=second_button_y,
    width=414.0,
    height=47.0
)


progress_bar = ttk.Progressbar(window, orient="horizontal", mode="determinate")
# Adjusted position for larger window
progress_bar.pack(padx=10, pady=500, side="bottom")

# Create and position the progress label
progress_label = tkinter.Label(window, text="", font=("Helvetica", 10))
progress_label.pack(side="bottom")

# Create and position the time remaining label
time_remaining = tkinter.Label(window, text="", font=("Helvetica", 10))
time_remaining.pack(side="bottom")


window.resizable(False, False)
window.mainloop()

# End of GUI Code
