import mcp4725_driver
import signal_generator
import time

# Параметры генерируемого сигнала
SIGNAL_FREQUENCY = 1.0      # Частота сигнала в герцах
AMPLITUDE = 2.5             # Амплитуда сигнала в вольтах (до 5.11В)
SAMPLING_FREQUENCY = 100    # Частота дискретизации в герцах
DYNAMIC_RANGE = 5.11        # Динамический диапазон ЦАП в вольтах

def main():
    """
    Основная функция для генерации синусоидального сигнала с использованием MCP4725
    """
    dac = None
    try:
        # Создаем объект класса для управления микросхемой MCP4725 по I2C
        dac = mcp4725_driver.MCP4725(
            dynamic_range=DYNAMIC_RANGE,
            address=0x61,
            verbose=True
        )
        
        print("Генерация синусоидального сигнала с использованием MCP4725:")
        print(f"  Частота сигнала: {SIGNAL_FREQUENCY} Гц")
        print(f"  Амплитуда: {AMPLITUDE} В")
        print(f"  Частота дискретизации: {SAMPLING_FREQUENCY} Гц")
        print(f"  Динамический диапазон: {DYNAMIC_RANGE} В")
        print("Для остановки нажмите Ctrl+C")
        
        start_time = time.time()
        
        # В бесконечном цикле генерируем сигнал
        while True:
            # Вычисляем текущее время с начала генерации
            current_time = time.time() - start_time
            
            # Получаем амплитуду сигнала в текущий момент времени
            signal_value = signal_generator.get_sin_wave_amplitude(
                SIGNAL_FREQUENCY, 
                current_time
            ) * AMPLITUDE
            
            # Подаем напряжение на пин OUT блока 12-bit DAC
            dac.set_voltage(signal_value)
            
            # Ждем до следующего периода дискретизации
            signal_generator.wait_for_sampling_period(SAMPLING_FREQUENCY)
            
    except KeyboardInterrupt:
        print("\nГенерация сигнала остановлена пользователем")
    
    

# Альтернативная версия с использованием функции generate_signal из signal_generator
def main_with_generate_signal():
    """
    Альтернативная реализация с использованием готовой функции generate_signal
    """
    dac = None
    try:
        # Создаем объект класса для управления микросхемой MCP4725 по I2C
        dac = mcp4725_driver.MCP4725(
            dynamic_range=DYNAMIC_RANGE,
            address=0x61,
            verbose=True
        )
        
        print("Генерация синусоидального сигнала с использованием MCP4725:")
        print(f"  Частота сигнала: {SIGNAL_FREQUENCY} Гц")
        print(f"  Амплитуда: {AMPLITUDE} В")
        print(f"  Частота дискретизации: {SAMPLING_FREQUENCY} Гц")
        print(f"  Динамический диапазон: {DYNAMIC_RANGE} В")
        print("Для остановки нажмите Ctrl+C")
        
        # Используем функцию generate_signal из модуля signal_generator
        signal_generator.generate_signal(
            dac=dac,
            signal_frequency=SIGNAL_FREQUENCY,
            amplitude=AMPLITUDE,
            sampling_frequency=SAMPLING_FREQUENCY,
            duration=None  # Бесконечная генерация
        )
            
    except KeyboardInterrupt:
        print("\nГенерация сигнала остановлена пользователем")
    """except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        # Вызываем «деструктор» объекта класса управления микросхемой MCP4725
        if dac is not None:
            dac.deinit()
            print("MCP4725 успешно отключен")"""

if __name__ == "__main__":
    # Запускаем основную функцию
    main()
    
    # Или альтернативную версию (раскомментируйте строку ниже)
    # main_with_generate_signal()