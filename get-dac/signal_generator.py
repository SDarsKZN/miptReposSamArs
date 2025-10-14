#import numpy
import time
import r2r_dac as r2r
import math

def get_sin_wave_amplitude(freq, time):
    sin_value = math.sin(2 * math.pi * freq * time)
    
    shifted_sin = sin_value + 1

    normalized_amplitude = shifted_sin / 2
    
    return normalized_amplitude

def wait_for_sampling_period(sampling_frequency):
    if sampling_frequency <= 0:
        raise ValueError("Частота дискретизации должна быть положительным числом")

    sampling_period = 1.0 / sampling_frequency
    
    time.sleep(sampling_period)

def generate_signal(dac, signal_frequency, amplitude, sampling_frequency, duration=None):
    start_time = time.time()
    
    if duration is None:
        while True:
            current_time = time.time() - start_time
            signal_value = get_sin_wave_amplitude(signal_frequency, current_time) * amplitude
            dac.set_voltage(signal_value)
            wait_for_sampling_period(sampling_frequency)
    else:
        end_time = start_time + duration
        while time.time() < end_time:
            current_time = time.time() - start_time
            signal_value = get_sin_wave_amplitude(signal_frequency, current_time) * amplitude
            dac.set_voltage(signal_value)
            wait_for_sampling_period(sampling_frequency)

if __name__ == "__main__":
    try:
        dac = r2r.R2R_DAC(
            gpio_bits=[16, 20, 21, 25, 26, 17, 27, 22],
            dynamic_range=3.16,
            verbose=True
        )

        SIGNAL_FREQUENCY = 10
        AMPLITUDE = 1.7       
        SAMPLING_FREQUENCY = 100000
        
        print("Геренация суицидального сигнала:")
        print(f"  Частота: {SIGNAL_FREQUENCY} Гц")
        print(f"  Амплитуда: {AMPLITUDE} В")
        print(f"  Частота дискретизации: {SAMPLING_FREQUENCY} Гц")
        print("Для остановки нажмите Ctrl+C")

        while True:
            generate_signal(
                dac=dac,
                signal_frequency=SIGNAL_FREQUENCY,
                amplitude=AMPLITUDE,
                sampling_frequency=SAMPLING_FREQUENCY,
                duration=None  
            )
            
    except KeyboardInterrupt:
        print("\nГенерация сигнала остановлена пользователем")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        dac.deinit()