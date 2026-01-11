from machine import Pin, PWM
import time
import neopixel
import os
import secrets  # secrets.py module with a dictionary called secrets

# Pin configuration
blue = Pin(6, Pin.OUT)
red = Pin(4, Pin.OUT)
green = Pin(5, Pin.OUT)

button = Pin(1, Pin.IN, Pin.PULL_UP)

# keep only the pin for the buzzer so it stays silent until initialised
buzzer_pin = Pin(8)

np = neopixel.NeoPixel(Pin(21), 1)

# Variables

# Duration thresholds (milliseconds)
GREEN_MAX_MS = int(secrets.secrets["GREEN_MAX_MS"])         # <=1s -> green
BLUE_MIN_MS = int(secrets.secrets["BLUE_MIN_MS"])          # >=3s -> blue (upper bound handled below)
BLUE_MAX_MS = int(secrets.secrets["BLUE_MAX_MS"])          # 3.000..4.999s -> blue
SIREN_THRESHOLD_MS = int(secrets.secrets["SIREN_THRESHOLD_MS"])   # >=5s -> alarm mode
ALARM_BLINK = float(secrets.secrets["ALARM_BLINK"])          # seconds per phase for alarm

# Buzzer settings
BEEP_MS = 750               # default beep length in ms
BEEP_FREQ = 2000            # default beep frequency in Hz
BEEP_DUTY = 32768           # duty for duty_u16


def set_led_color(color):
    if color == "blue":
        blue.value(1)
        green.value(0)
        red.value(0)
    elif color == "green":
        blue.value(0)
        green.value(1)
        red.value(0)
    elif color == "red":
        blue.value(0)
        green.value(0)
        red.value(1)
    else:
        blue.value(0)
        green.value(0)
        red.value(0)


def show_state(state):
    if state == 'green':
        print('STATE: Veilig')
        set_led_color('green')
        np[0] = (150, 0, 0)
    elif state == 'red':
        set_led_color('red')
        np[0] = (0, 120, 0)
    elif state == 'blue':
        print('STATE: Risico')
        set_led_color('blue')
        np[0] = (0, 0, 150)
    else:
        print('STATE: IDLE')
        set_led_color('green')
        # Use same NeoPixel color as the 'green' state so idle is visually green
        np[0] = (150, 0, 0)
    np.write()

# Persistent PWM instance for buzzer (created on first use)
pwm_buzzer = None

def init_buzzer_pwm(freq=BEEP_FREQ):
    global pwm_buzzer
    try:
        pwm_buzzer = PWM(buzzer_pin)
        pwm_buzzer.freq(freq)
        # ensure buzzer is silent initially
        try:
            pwm_buzzer.duty_u16(0)
        except AttributeError:
            pwm_buzzer.duty(0)
        return True
    except Exception as e:
        pwm_buzzer = None
        print("PWM init failed for buzzer:", e)
        return False


def beep(ms=BEEP_MS, freq=BEEP_FREQ, duty=BEEP_DUTY):
    # Play a short tone using PWM
    global pwm_buzzer
    if pwm_buzzer is None:
        init_buzzer_pwm(freq)
    if pwm_buzzer:
        try:
            pwm_buzzer.freq(freq)
            pwm_buzzer.duty_u16(duty)
            time.sleep_ms(ms)
            # silence
            pwm_buzzer.duty_u16(0)
            pwm_buzzer.duty(0)
            return
        except Exception as e:
            print("PWM beep failed:", e)
    time.sleep_ms(ms)

# Vibration sensor on Pin 7
# Wiring: VCC -> 3.3V, GND -> GND, OUT -> GPIO7
try:
    vibration = Pin(7, Pin.IN, Pin.PULL_DOWN)
    pull_mode = 'PULL_DOWN'
except Exception:
    vibration = Pin(7, Pin.IN)
    pull_mode = 'NONE'

print("Starting vibration readout on pin 7 (pull: {})...".format(pull_mode))
# Simple detector parameters
SAMPLE_WINDOW = 6
THRESHOLD = 0.4
ACTIVITY_HOLD_MS = 300   # keep 'vibrating' for short pulses

# rolling window and last spike timestamp
_window = [0] * SAMPLE_WINDOW
_last_raw_high = None

INVERT_LOGIC = True
def read_raw():
    v = vibration.value()
    if INVERT_LOGIC:
        v = not v
    return 1 if v else 0


def is_vibrating():
    # Update rolling window, track recent spikes, and return True if activity is present.
    global _last_raw_high
    raw = read_raw()
    # update rolling window
    _window.pop(0)
    _window.append(raw)

    now = time.ticks_ms()
    if raw:
        _last_raw_high = now
        return True
    # hold activity for short pulses
    if _last_raw_high and time.ticks_diff(now, _last_raw_high) <= ACTIVITY_HOLD_MS:
        return True
    # window-based threshold
    if sum(_window) / SAMPLE_WINDOW >= THRESHOLD:
        return True
    return False

# Quick idle baseline check to detect floating pin and try pull-up fallback if needed
_idle_sum = 0
for _ in range(10):
    _idle_sum += read_raw()
    time.sleep(0.005)
_idle_ratio = _idle_sum / 10.0
print("Idle high ratio: {:.2f}".format(_idle_ratio))
if _idle_ratio > 0.4 and pull_mode != 'PULL_UP':
    print("Idle high -> trying internal pull-up and inverting logic (useful for SW-520)")
    try:
        vibration = Pin(7, Pin.IN, Pin.PULL_UP)
        INVERT_LOGIC = True
        pull_mode = 'PULL_UP'
        # resample
        _idle_sum = 0
        for _ in range(10):
            _idle_sum += read_raw()
            time.sleep(0.005)
        _idle_ratio = _idle_sum / 10.0
        print("After PULL_UP, idle high ratio: {:.2f}".format(_idle_ratio))
    except Exception:
        print("Could not enable PULL_UP on this pin; consider adding external pull-down.")

if _idle_ratio > 0.6:
    print("Warning: pin still reads HIGH at idle. Please add a 10k pull-down to GPIO7 or use a different pin with a pull-down.")
# Logging variables
last_vibration_end_ms = None
last_vibration_duration_ms = 0
LOG_INTERVAL_MS = 3000
_last_log_ms = time.ticks_ms()

vibration_start = None
last_state = None
current_state = None
# If we enter GEVAAR (red), latch it until user acknowledges with the button on pin 1.
red_latched = False
# Prevent immediate override of green after clearing latch
just_cleared_latch = False

def _format_time_ms(ms):
    if ms is None:
        return 'never'
    try:
        sec = ms // 1000
        t = time.localtime(sec)
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(t[0], t[1], t[2], t[3], t[4], t[5])
    except Exception:
        return "{}s since boot".format(ms // 1000)




def alarm():
    global last_vibration_end_ms, last_vibration_duration_ms, vibration_start, current_state
    print("Entering alarm mode")
    while is_vibrating():
        set_led_color('red')
        np[0] = (0, 200, 0)
        np.write()
        # short audible beep using PWM
        beep(BEEP_MS)
        # pause remainder of the blink period
        time.sleep(max(0, ALARM_BLINK - (BEEP_MS / 1000.0)))

        set_led_color('off')
        np[0] = (0, 0, 0)
        np.write()
        time.sleep(ALARM_BLINK)
    # vibration ended while in alarm
    end_ms = time.ticks_ms()
    if vibration_start is not None:
        last_vibration_end_ms = end_ms
        last_vibration_duration_ms = time.ticks_diff(end_ms, vibration_start)
    print("Exiting alarm mode")
    # Do not reset state here; wait for button press to return to 'veilig'

# Main loop (concise and responsive)
while True:
    now = time.ticks_ms()
    active = is_vibrating()

    if active:
        just_cleared_latch = False  # reset if vibration resumes
        if vibration_start is None:
            vibration_start = now
        elapsed = time.ticks_diff(now, vibration_start)

        if elapsed <= 1000:
            state = 'green'
        elif elapsed < 3000:
            state = 'red'
        elif elapsed < 5000:
            state = 'blue'
        else:
            state = 'siren'


        # Only latch in SIREN (alarm) state
        if state == 'siren':
            if not red_latched:
                print("ALARM: press button to return to VEILIG")
                try:
                    beep(300, freq=800, duty=40000)
                except Exception as e:
                    print("Beep (alarm) failed:", e)
                red_latched = True
        else:
            # In any state other than SIREN, clear latch automatically
            if red_latched:
                red_latched = False
                just_cleared_latch = True

        if state == 'siren':
            if not red_latched:
                alarm()
                # After alarm, stay in siren state until button is pressed
                last_state = 'siren'
                current_state = 'siren'
                vibration_start = None
            # While latched, keep running alarm effect
            while red_latched:
                # Blinking red effect (same as alarm)
                set_led_color('red')
                np[0] = (0, 200, 0)
                np.write()
                beep(BEEP_MS)
                time.sleep(max(0, ALARM_BLINK - (BEEP_MS / 1000.0)))
                set_led_color('off')
                np[0] = (0, 0, 0)
                np.write()
                time.sleep(ALARM_BLINK)
                # Check for button press to clear latch
                if button.value() == 0:
                    time.sleep(0.05)
                    if button.value() == 0:
                        try:
                            beep(100, freq=2000, duty=30000)
                            time.sleep(0.08)
                            beep(100, freq=2200, duty=30000)
                        except Exception as e:
                            print("Beep (ack) failed:", e)
                        print("Button pressed: clearing ALARM -> VEILIG")
                        red_latched = False
                        show_state('green')
                        last_state = 'green'
                        current_state = 'green'
                        just_cleared_latch = True
                        # Wait for button release
                        while button.value() == 0:
                            time.sleep(0.01)
                        # Wait for vibration to stop before allowing alarm to re-trigger
                        while is_vibrating():
                            time.sleep(0.05)
            continue

        if last_state != state:
            show_state(state)
            last_state = state
            current_state = state

    else:
        # if vibration just ended, record end time and duration
        if vibration_start is not None:
            end_ms = now
            last_vibration_end_ms = end_ms
            last_vibration_duration_ms = time.ticks_diff(end_ms, vibration_start)
            vibration_start = None

        # If siren is latched, do not switch to IDLE or green automatically
        if not red_latched and not just_cleared_latch:
            if last_state != 'no_vibration':
                show_state('no_vibration')
                last_state = 'no_vibration'
                current_state = 'no_vibration'
        if just_cleared_latch:
            just_cleared_latch = False

    # periodic logging every LOG_INTERVAL_MS
    if time.ticks_diff(now, _last_log_ms) >= LOG_INTERVAL_MS:
        _last_log_ms = now
        ts = _format_time_ms(last_vibration_end_ms)
        dur = last_vibration_duration_ms
        if dur:
            print("LOG: last vibration at {} (duration {} ms)".format(ts, dur))
        else:
            print("LOG: no vibrations recorded yet")
        # Add current state log
        print("LOG: current state is {}".format(current_state))


    # If SIREN is latched, keep showing siren/alarm until acknowledged by the button.
    if red_latched:
        if current_state != 'siren':
            if last_state != 'siren':
                show_state('siren')
                last_state = 'siren'
                current_state = 'siren'
        # button is pull-up; pressed when value() == 0
        if button.value() == 0:
            # debounce short
            time.sleep(0.05)
            if button.value() == 0:
                # acknowledgement tone (two short high-pitched beeps)
                try:
                    beep(100, freq=2000, duty=30000)
                    time.sleep(0.08)
                    beep(100, freq=2200, duty=30000)
                except Exception as e:
                    print("Beep (ack) failed:", e)
                print("Button pressed: clearing ALARM -> VEILIG")
                red_latched = False
                show_state('green')
                last_state = 'green'
                current_state = 'green'
                just_cleared_latch = True
                # wait for button release to avoid multiple triggers
                while button.value() == 0:
                    time.sleep(0.01)

    time.sleep(0.02)
