import numpy
import time
import r2r_dac as r2r
import math

def get_sin_wave_amplitude(freq, time):
    """
    Вычисляет амплитуду синусоидального сигнала в заданный момент времени.
    
    Args:
        freq (float): Частота сигнала в герцах
        time (float): Момент времени в секундах
    
    Returns:
        float: Амплитуда в диапазоне от 0 до 1
    """
    # Вычисляем значение синуса в заданный момент времени
    sin_value = math.sin(2 * math.pi * freq * time)
    
    # Сдвигаем синус вверх: от [-1, 1] к [0, 2]
    shifted_sin = sin_value + 1
    
    # Нормализуем к диапазону [0, 1]
    normalized_amplitude = shifted_sin / 2
    
    return normalized_amplitude

def wait_for_sampling_period(sampling_frequency):
    """
    Ожидает в течение одного периода дискретизации.
    
    Args:
        sampling_frequency (float): Частота дискретизации в герцах
    """
    if sampling_frequency <= 0:
        raise ValueError("Частота дискретизации должна быть положительным числом")
    
    # Вычисляем период дискретизации в секундах
    sampling_period = 1.0 / sampling_frequency
    
    # Ожидаем в течение периода дискретизации
    time.sleep(sampling_period)

def generate_signal(dac, signal_frequency, amplitude, sampling_frequency, duration=None):
    """
    Генерирует сигнал и подает его на ЦАП.
    
    Args:
        dac: Объект ЦАП
        signal_frequency (float): Частота сигнала в герцах
        amplitude (float): Амплитуда сигнала в вольтах
        sampling_frequency (float): Частота дискретизации в герцах
        duration (float, optional): Длительность генерации в секундах. Если None - бесконечная генерация
    """
    start_time = time.time()
    
    if duration is None:
        # Бесконечная генерация
        while True:
            current_time = time.time() - start_time
            signal_value = get_sin_wave_amplitude(signal_frequency, current_time) * amplitude
            dac.set_voltage(signal_value)
            wait_for_sampling_period(sampling_frequency)
    else:
        # Генерация в течение заданного времени
        end_time = start_time + duration
        while time.time() < end_time:
            current_time = time.time() - start_time
            signal_value = get_sin_wave_amplitude(signal_frequency, current_time) * amplitude
            dac.set_voltage(signal_value)
            wait_for_sampling_period(sampling_frequency)

# Основная программа
if __name__ == "__main__":
    try:
        # Создаем объект класса для управления R2R-ЦАП
        # Используем те же параметры, что и в файле r2r_dac.py
        dac = r2r.R2R_DAC(
            gpio_bits=[16, 20, 21, 25, 26, 17, 27, 22],
            dynamic_range=3.16,
            verbose=True
        )
        
        # Параметры сигнала
        SIGNAL_FREQUENCY = 1.0      # 1 Гц
        AMPLITUDE = 1.5             # 1.5 В
        SAMPLING_FREQUENCY = 100    # 100 Гц (100 отсчетов в секунду)
        
        print(f"Генерация синусоидального сигнала:")
        print(f"  Частота: {SIGNAL_FREQUENCY} Гц")
        print(f"  Амплитуда: {AMPLITUDE} В")
        print(f"  Частота дискретизации: {SAMPLING_FREQUENCY} Гц")
        print("Для остановки нажмите Ctrl+C")
        
        # В бесконечном цикле генерируем сигнал
        while True:
            generate_signal(
                dac=dac,
                signal_frequency=SIGNAL_FREQUENCY,
                amplitude=AMPLITUDE,
                sampling_frequency=SAMPLING_FREQUENCY,
                duration=None  # Бесконечная генерация
            )
            
    except KeyboardInterrupt:
        print("\nГенерация сигнала остановлена пользователем")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        # Вызываем «деструктор» объекта класса управления R2R-ЦАП
        try:
            dac.deinit()
            print("ЦАП успешно отключен")
        except:
            print("Ошибка при отключении ЦАП")