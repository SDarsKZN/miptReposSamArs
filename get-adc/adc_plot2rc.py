import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt
import numpy as np

class R2R_ADC:
    def __init__(self, dynamic_range, compare_time=0.001, verbose=True):
        self.dynamic_range = dynamic_range
        self.verbose = verbose
        self.compare_time = compare_time
        
        self.bits_gpio = [26, 20, 19, 16, 13, 12, 25, 11]
        self.comp_gpio = 21

        print(f"Пины ЦАП: {self.bits_gpio}")
        print(f"Пин компаратора: {self.comp_gpio}")
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.bits_gpio, GPIO.OUT, initial=0)
        GPIO.setup(self.comp_gpio, GPIO.IN)
        
        # Протестируем компаратор
        print("Тестирование компаратора...")
        self.number_to_dac(0)
        time.sleep(0.1)
        comp_state_low = GPIO.input(self.comp_gpio)
        
        self.number_to_dac(255)
        time.sleep(0.1)
        comp_state_high = GPIO.input(self.comp_gpio)
        
        print(f"Состояние компаратора (ЦАП=0): {comp_state_low}")
        print(f"Состояние компаратора (ЦАП=255): {comp_state_high}")
    
    def __del__(self):
        GPIO.output(self.bits_gpio, 0)
        GPIO.cleanup()
    
    def number_to_dac(self, number):
        binary = format(number, '08b')
        for i, pin in enumerate(self.bits_gpio):
            GPIO.output(pin, int(binary[i]))
    
    def test_comparator(self):
        print("\nТестирование компаратора на разных значениях ЦАП:")
        test_values = [0, 64, 128, 192, 255]
        
        for val in test_values:
            self.number_to_dac(val)
            time.sleep(0.1)
            comp_state = GPIO.input(self.comp_gpio)
            voltage = (val / 255) * self.dynamic_range
            print(f"ЦАП={val:3d} ({voltage:.2f} В) -> Компаратор: {comp_state}")
    
    def fast_sequential_adc(self):
        """Быстрый последовательный АЦП с измерением времени выполнения"""
        start_measure_time = time.time()
        
        if self.verbose:
            print("Начало измерения АЦП...")
            
        for number in range(256):
            self.number_to_dac(number)
            time.sleep(self.compare_time)
            
            comp_state = GPIO.input(self.comp_gpio)
            
            if self.verbose and number % 32 == 0:
                voltage = (number / 255) * self.dynamic_range
                print(f"Шаг {number:3d} ({voltage:.2f} В) -> Компаратор: {comp_state}")
            
            if comp_state == 1:
                if self.verbose:
                    print(f"Найден переход при числе: {number}")
                measurement_time = time.time() - start_measure_time
                return number, measurement_time
        
        measurement_time = time.time() - start_measure_time
        return 255, measurement_time
    
    def get_sc_voltage(self):
        """Возвращает измеренное напряжение в Вольтах и время измерения"""
        digital_value, measurement_time = self.fast_sequential_adc()
        voltage = (digital_value / 255) * self.dynamic_range
        return voltage, measurement_time


def plot_voltage_vs_time(time_data, voltage_data, max_voltage):
    plt.figure(figsize=(12, 6))
    plt.plot(time_data, voltage_data, 'b-', linewidth=1, marker='o', markersize=3, label='Измеренное напряжение')
    plt.title('Зависимость напряжения от времени')
    plt.xlabel('Время, с')
    plt.ylabel('Напряжение, В')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(0, max_voltage * 1.1)
    if time_data:
        plt.xlim(0, max(time_data))
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_sampling_period_hist(measurement_times):
    """Строит распределение количества измерений по их продолжительности"""
    if not measurement_times:
        print("Нет данных для построения гистограммы")
        return
    
    # Создаем список для хранения промежутка времени, потраченного на каждое измерение
    sampling_periods = measurement_times
    
    print(f"Всего измерений: {len(sampling_periods)}")
    print(f"Времена измерений: {[f'{t:.3f}' for t in sampling_periods[:10]]}...")
    
    # Создаем окно для отображения графика
    plt.figure(figsize=(10, 6))
    
    # Размещаем гистограмму периодов измерений
    plt.hist(sampling_periods, bins=20, color='lightblue', edgecolor='black', alpha=0.7)
    
    # Задаем название графика и осей
    plt.title('Распределение продолжительности измерений АЦП')
    plt.xlabel('Продолжительность измерения, с')
    plt.ylabel('Количество измерений')
    
    # Задаем границы по оси X
    plt.xlim(0, 0.06)
    
    # Включаем отображение сетки
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Добавляем статистику
    mean_time = np.mean(sampling_periods)
    plt.axvline(mean_time, color='red', linestyle='--', label=f'Среднее: {mean_time:.3f} с')
    plt.legend()
    
    print(f"\n=== СТАТИСТИКА ПРОДОЛЖИТЕЛЬНОСТИ ИЗМЕРЕНИЙ ===")
    print(f"Среднее время измерения: {mean_time:.3f} с")
    print(f"Минимальное время: {min(sampling_periods):.3f} с")
    print(f"Максимальное время: {max(sampling_periods):.3f} с")
    print(f"Стандартное отклонение: {np.std(sampling_periods):.3f} с")
    
    plt.tight_layout()
    plt.show()


# Основной скрипт
if __name__ == "__main__":
    voltage_values = []
    time_values = []
    measurement_times = []  # Список для хранения времени каждого измерения
    duration = 15.0
    
    adc = None
    try:
        print("=== ПРОВЕРКА ПОДКЛЮЧЕНИЯ ===")
        print("Физические пины на Raspberry Pi:")
        print("GPIO26 -> физический пин 37")
        print("GPIO20 -> физический пин 38") 
        print("GPIO21 -> физический пин 40 (компаратор)")
        print("Убедитесь, что компаратор подключен к правильному пину!\n")
        
        adc = R2R_ADC(dynamic_range=3.3, verbose=False)
        
        start_time = time.time()
        measurement_count = 0
        
        print("Начало измерений...")
        print("Меняйте входное напряжение на компараторе во время измерений!")
        
        while (time.time() - start_time) < duration:
            current_time = time.time() - start_time
            
            # Получаем напряжение и время измерения
            voltage, measurement_time = adc.get_sc_voltage()
            
            voltage_values.append(voltage)
            time_values.append(current_time)
            measurement_times.append(measurement_time)
            measurement_count += 1
            
            print(f"Измерение {measurement_count:3d}: Время {current_time:5.1f} с, Напряжение: {voltage:.2f} В, Длительность: {measurement_time:.3f} с")
            
            time.sleep(0.1)  # Небольшая пауза между измерениями
        
        print(f"\nИзмерения завершены! Всего измерений: {measurement_count}")
        
        # Отображаем график напряжения
        plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range)
        
        # Отображаем гистограмму времени измерений
        plot_sampling_period_hist(measurement_times)
        
    except KeyboardInterrupt:
        print(f"\nИзмерения прерваны. Всего измерений: {len(voltage_values)}")
        if voltage_values:
            plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range if adc else 3.3)
        if measurement_times:
            plot_sampling_period_hist(measurement_times)
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if adc is not None:
            adc.__del__()
        print("Программа завершена")