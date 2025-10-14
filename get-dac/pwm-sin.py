import pwm_dac
import signal_generator
import time

SIGNAL_FREQUENCY = 1.0     
AMPLITUDE = 1.5           
SAMPLING_FREQUENCY = 100    
PWM_FREQUENCY = 500        
DYNAMIC_RANGE = 3.29        

def main():
    dac = None
    try:
        dac = pwm_dac.PWM_DAC(
            gpio_pin=12,
            pwm_frequency=PWM_FREQUENCY,
            dynamic_range=DYNAMIC_RANGE,
            verbose=True
        )
        
        print("Генерация синусоидального сигнала с использованием PWM DAC:")
        print(f"  Частота сигнала: {SIGNAL_FREQUENCY} Гц")
        print(f"  Амплитуда: {AMPLITUDE} В")
        print(f"  Частота дискретизации: {SAMPLING_FREQUENCY} Гц")
        print(f"  Частота ШИМ: {PWM_FREQUENCY} Гц")
        print(f"  Динамический диапазон: {DYNAMIC_RANGE} В")
        print("Для остановки нажмите Ctrl+C")
        
        start_time = time.time()
        
        while True:
            current_time = time.time() - start_time
            
            signal_value = signal_generator.get_sin_wave_amplitude(
                SIGNAL_FREQUENCY, 
                current_time
            ) * AMPLITUDE
            
            dac.set_voltage(signal_value)

            signal_generator.wait_for_sampling_period(SAMPLING_FREQUENCY)
            
    except KeyboardInterrupt:
        print("\nГенерация сигнала остановлена пользователем")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        if dac is not None:
            dac.deinit()
            print("PWM DAC успешно отключен")

def main_with_generate_signal():
    """
    Альтернативная реализация с использованием готовой функции generate_signal
    """
    dac = None
    try:
        dac = pwm_dac.PWM_DAC(
            gpio_pin=12,
            pwm_frequency=PWM_FREQUENCY,
            dynamic_range=DYNAMIC_RANGE,
            verbose=True
        )
        
        print("Генерация синусоидального сигнала с использованием PWM DAC:")
        print(f"  Частота сигнала: {SIGNAL_FREQUENCY} Гц")
        print(f"  Амплитуда: {AMPLITUDE} В")
        print(f"  Частота дискретизации: {SAMPLING_FREQUENCY} Гц")
        print(f"  Частота ШИМ: {PWM_FREQUENCY} Гц")
        print(f"  Динамический диапазон: {DYNAMIC_RANGE} В")
        print("Для остановки нажмите Ctrl+C")
        
        signal_generator.generate_signal(
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
        if dac is not None:
            dac.deinit()
            print("PWM DAC успешно отключен")

if __name__ == "__main__":
    main()
    