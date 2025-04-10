import pygame
import os
import glob
import threading
import time
from collections import deque
import json  # To save/load baseline data

# Optimize Pygame Display
os.environ["SDL_VIDEODRIVER"] = "wayland"

# Initialize Pygame
pygame.init()

# Get Screen Size
SCREEN_WIDTH = pygame.display.Info().current_w
SCREEN_HEIGHT = pygame.display.Info().current_h

# Constants
BARS = 256
MAX_BAR_HEIGHT = (SCREEN_HEIGHT // 1.1) - 32
LINE_COLOR = (255, 255, 0)
LINE_THICKNESS = 5
SWITCH_TIMEOUT = 20

# Sensitivity control
sensitivity = 1.0

# Baseline noise removal
baseline_data = []
collecting_baseline = False
baseline_start_time = 0
baseline_buffer = deque(maxlen=180)

# File path to store baseline data
baseline_file = "/home/pi/Projects/cava-pygame/baseline_data.json"

# Setup Pygame Display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

# Load and Pre-Scale Background Images
background_folder = "/home/pi/Projects/cava-pygame/backgrounds"
background_images = sorted(glob.glob(os.path.join(background_folder, "*.png")))

if not background_images:
    raise FileNotFoundError("No background images found in 'backgrounds/' folder!")

backgrounds = [pygame.transform.scale(pygame.image.load(img), (SCREEN_WIDTH, SCREEN_HEIGHT)) for img in background_images]
bg_index = 0
last_switch_time = time.time()

# Open FIFO for CAVA Data
fifo_path = "/tmp/cava.fifo"
if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)

# Shared Data Storage
cava_data = [0] * BARS
data_lock = threading.Lock()

# Non-Blocking CAVA Data Reader
def read_cava_data():
    global cava_data
    with open(fifo_path, "r") as fifo:
        for line in fifo:
            data = [int(x) for x in line.strip().split(";") if x.strip().isdigit()]
            if data:
                with data_lock:
                    cava_data = data[:-158] if len(data) > 158 else data

# Start CAVA Reader Thread
cava_thread = threading.Thread(target=read_cava_data, daemon=True)
cava_thread.start()

# Function to render the countdown and message
def render_countdown(countdown_time):
    font = pygame.font.SysFont("Arial", 50)
    text = font.render(f"Quiet on the set - Baseline recording in progress.....", True, (255, 0, 0))
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    screen.blit(text, text_rect)

    font = pygame.font.SysFont("Arial", 100)
    text = font.render(str(countdown_time), True, (255, 0, 0))
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(text, text_rect)

# Function to save baseline data
def save_baseline():
    global baseline_data
    with open(baseline_file, "w") as f:
        json.dump(baseline_data, f)
    print("[INFO] Baseline saved.")

# Function to load baseline data
def load_baseline():
    global baseline_data
    if os.path.exists(baseline_file):
        with open(baseline_file, "r") as f:
            baseline_data = json.load(f)
        print("[INFO] Baseline loaded.")
    else:
        print("[INFO] No baseline file found. Please record a baseline.")

# Main Loop
clock = pygame.time.Clock()
running = True

load_baseline()  # Load baseline at startup

while running:
    if bg_index in [1, 2] and time.time() - last_switch_time > SWITCH_TIMEOUT:
        bg_index = 0
        last_switch_time = time.time()

    screen.blit(backgrounds[bg_index], (0, 0))

    if bg_index == 0:
        with data_lock:
            local_cava_data = cava_data[:]

        if baseline_data and len(local_cava_data) == len(baseline_data):
            filtered_data = [max(val - base, 0) for val, base in zip(local_cava_data, baseline_data)]
        else:
            filtered_data = local_cava_data

        if collecting_baseline:
            elapsed_time = time.time() - baseline_start_time
            if elapsed_time < 10:
                # Update baseline buffer
                baseline_buffer.append(local_cava_data[:])
                countdown_time = int(10 - elapsed_time)  # Countdown from 10 seconds
                render_countdown(countdown_time)
            else:
                # Calculate baseline after 10 seconds
                num_samples = len(baseline_buffer)
                if num_samples > 0:
                    baseline_data = [
                        int(sum(sample[i] for sample in baseline_buffer) / num_samples)
                        for i in range(len(baseline_buffer[0]))
                    ]
                    save_baseline()  # Save the baseline after recording
                    collecting_baseline = False
                    print("[INFO] New baseline recorded.")
        else:
            # Render the graph as normal after baseline collection
            BARS = len(filtered_data)
            POINT_SPACING = SCREEN_WIDTH / (BARS - 1)
            center_y = SCREEN_HEIGHT // 2

            upper_wave = [
                (i * POINT_SPACING, center_y - max(2, min(int(val * sensitivity), MAX_BAR_HEIGHT)) // 2)
                for i, val in enumerate(filtered_data)
            ]
            lower_wave = [(x, 2 * center_y - y) for x, y in upper_wave]

            if len(upper_wave) > 1:
                pygame.draw.lines(screen, LINE_COLOR, False, upper_wave, LINE_THICKNESS)
                pygame.draw.lines(screen, LINE_COLOR, False, lower_wave, LINE_THICKNESS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                key_number = event.key - pygame.K_1
                if key_number < len(backgrounds):
                    bg_index = key_number
                    last_switch_time = time.time()
            elif event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_UP:
                sensitivity = min(sensitivity + 0.1, 5.0)
                print(f"Sensitivity increased to {sensitivity:.1f}")
            elif event.key == pygame.K_DOWN:
                sensitivity = max(sensitivity - 0.1, 0.1)
                print(f"Sensitivity decreased to {sensitivity:.1f}")
            elif event.key == pygame.K_b:
                collecting_baseline = True
                baseline_start_time = time.time()
                baseline_buffer.clear()
                print("[INFO] Manual baseline recording started...")

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
