import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt
import numpy as np

class R2R_ADC:
    def __init__(self, dynamic_range, compare_time=0.001, verbose=False):
        self.dynamic_range = dynamic_range
        self.verbose = verbose
        self.compare_time = compare_time
        
        self.bits_gpio = [26, 20, 19, 16, 13, 12, 25, 11]
        self.comp_gpio = 21

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.bits_gpio, GPIO.OUT, initial=0)
        GPIO.setup(self.comp_gpio, GPIO.IN)
    
    def __del__(self):
        """Деструктор - выставляет 0 на выход ЦАП и очищает настройки GPIO"""
        GPIO.output(self.bits_gpio, 0)
        GPIO.cleanup()
    
    def number_to_dac(self, number):
        """Подает число number на вход ЦАП"""
        binary = format(number, '08b')
        for i, pin in enumerate(self.bits_gpio):
            GPIO.output(pin, int(binary[i]))
    
    def successive_approximation_adc(self):
        """Реализует алгоритм бинарного поиска напряжения на входе АЦП"""
        start_measure_time = time.time()
        
        if self.verbose:
            print("Начало измерения методом последовательного приближения (SAR)...")
        
        # Начинаем со среднего значения 8-битного диапазона
        result = 0
        # Маска для установки битов, начиная со старшего
        bit_mask = 0b10000000  # 128 в десятичной
        
        for _ in range(8):  # 8 итераций для 8-битного АЦП
            # Устанавливаем текущий бит
            test_value = result | bit_mask
            self.number_to_dac(test_value)
            time.sleep(self.compare_time)
            
            # Читаем состояние компаратора
            comp_state = GPIO.input(self.comp_gpio)
            
            if self.verbose:
                voltage = (test_value / 255) * self.dynamic_range
                print(f"Тестовое значение: {test_value:3d} ({voltage:.2f} В) -> Компаратор: {comp_state}")
            
            if comp_state == 0:
                # U_DAC < U_ADC - оставляем бит установленным
                result = test_value
                if self.verbose:
                    print(f"  Бит установлен: {bin(test_value)}")
            else:
                # U_DAC > U_ADC - сбрасываем бит
                if self.verbose:
                    print(f"  Бит сброшен")
            
            # Переходим к следующему биту
            bit_mask = bit_mask >> 1
        
        measurement_time = time.time() - start_measure_time
        
        if self.verbose:
            print(f"Результат SAR: {result}, Время измерения: {measurement_time:.3f} с")
        
        return result, measurement_time

    def get_sar_voltage(self):
        """Возвращает измеренное алгоритмом бинарного поиска напряжение в Вольтах и время измерения"""
        digital_value, measurement_time = self.successive_approximation_adc()
        voltage = (digital_value / 255) * self.dynamic_range
        return voltage, measurement_time


def plot_voltage_vs_time(time_data, voltage_data, max_voltage):
    """Строит график зависимости напряжения от времени"""
    plt.figure(figsize=(12, 6))
    plt.plot(time_data, voltage_data, 'b-', linewidth=2, marker='o', markersize=4, label='Напряжение (SAR метод)')
    plt.title('Зависимость напряжения от времени (Алгоритм бинарного поиска)')
    plt.xlabel('Время, с')
    plt.ylabel('Напряжение, В')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(0, max_voltage * 1.1)
    if time_data:
        plt.xlim(0, max(time_data))
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_sampling_period_hist(measurement_times, method_name="SAR"):
    """Строит распределение количества измерений по их продолжительности"""
    if not measurement_times:
        print("Нет данных для построения гистограммы")
        return
    
    sampling_periods = measurement_times
    
    print(f"Всего измерений ({method_name}): {len(sampling_periods)}")
    print(f"Времена измерений (первые 10): {[f'{t:.3f}' for t in sampling_periods[:10]]}")
    
    plt.figure(figsize=(10, 6))
    
    # Создаем бины с периодом 0.01 секунды (SAR метод быстрее)
    bins = np.arange(0, max(sampling_periods) + 0.01, 0.01)
    
    n, bins, patches = plt.hist(sampling_periods, bins=bins, color='lightgreen', 
                               edgecolor='black', alpha=0.7, rwidth=0.8)
    
    plt.title(f'Распределение продолжительности измерений АЦП ({method_name} метод)')
    plt.xlabel('Продолжительность измерения, с')
    plt.ylabel('Количество измерений')
    
    plt.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    # Добавляем подписи к столбцам
    for i in range(len(n)):
        if n[i] > 0:
            plt.text(bins[i] + 0.005, n[i] + 0.1, str(int(n[i])), 
                    ha='center', va='bottom', fontsize=9)
    
    mean_time = np.mean(sampling_periods)
    plt.axvline(mean_time, color='red', linestyle='--', linewidth=2, 
               label=f'Среднее: {mean_time:.3f} с')
    
    plt.text(0.02, 0.95, f'Бины: по 0.01 с', 
            transform=plt.gca().transAxes, fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    plt.text(0.02, 0.85, f'Всего измерений: {len(sampling_periods)}', 
            transform=plt.gca().transAxes, fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    plt.legend()
    
    print(f"\n=== СТАТИСТИКА ПРОДОЛЖИТЕЛЬНОСТИ ИЗМЕРЕНИЙ ({method_name}) ===")
    print(f"Среднее время измерения: {mean_time:.3f} с")
    print(f"Минимальное время: {min(sampling_periods):.3f} с")
    print(f"Максимальное время: {max(sampling_periods):.3f} с")
    print(f"Стандартное отклонение: {np.std(sampling_periods):.3f} с")
    print(f"Частота измерений: {1/mean_time:.1f} Гц")
    print(f"\nРаспределение по бинам:")
    for i in range(len(n)):
        if n[i] > 0:
            print(f"  {bins[i]:.2f}-{bins[i+1]:.2f} с: {int(n[i])} измерений")
    
    plt.tight_layout()
    plt.show()


# Основной скрипт для визуализации SAR измерений с гистограммой
if __name__ == "__main__":
    # Настраиваемые параметры
    DYNAMIC_RANGE = 3.3  # Динамический диапазон ЦАП в Вольтах
    DURATION = 10.0      # Продолжительность измерений в секундах
    
    print("=== SAR АЦП - Визуализация напряжения и гистограмма времени измерений ===")
    print(f"Динамический диапазон: {DYNAMIC_RANGE} В")
    print(f"Продолжительность измерений: {DURATION} с")
    print("Для досрочного завершения нажмите Ctrl+C\n")
    
    # Списки для данных
    voltage_values = []      # Для хранения напряжений
    time_values = []         # Для хранения моментов времени от старта скрипта
    measurement_times = []   # Для хранения времени каждого измерения SAR
    
    adc = None
    try:
        # Создаем объект класса R2R_ADC
        adc = R2R_ADC(dynamic_range=DYNAMIC_RANGE, compare_time=0.001, verbose=False)
        
        start_time = time.time()
        measurement_count = 0
        
        print("Начало измерений методом последовательного приближения (SAR)...")
        print("Изменяйте напряжение потенциометра для наблюдения изменений на графике")
        
        while (time.time() - start_time) < DURATION:
            current_time = time.time() - start_time
            
            # Получаем напряжение и время измерения
            voltage, measurement_time = adc.get_sar_voltage()
            
            voltage_values.append(voltage)
            time_values.append(current_time)
            measurement_times.append(measurement_time)
            measurement_count += 1
            
            # Выводим прогресс
            progress = (current_time / DURATION) * 100
            print(f"Прогресс: {progress:5.1f}% | Измерение {measurement_count:3d}: {current_time:5.1f} с, Напряжение: {voltage:.2f} В, Время изм.: {measurement_time:.3f} с")
            
            # Небольшая пауза для стабильности измерений
            time.sleep(0.05)
        
        print(f"\nИзмерения завершены! Всего измерений: {measurement_count}")
        
        # Отображаем график напряжения
        print("\nПостроение графика зависимости напряжения от времени...")
        plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range)
        
        # Отображаем гистограмму времени измерений
        print("\nПостроение гистограммы времени измерений...")
        plot_sampling_period_hist(measurement_times, "SAR")
        
    except KeyboardInterrupt:
        print(f"\nИзмерения прерваны пользователем")
        if voltage_values:
            print(f"Всего выполнено измерений: {len(voltage_values)}")
            print("Построение графиков по собранным данным...")
            plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range if adc else DYNAMIC_RANGE)
            if measurement_times:
                plot_sampling_period_hist(measurement_times, "SAR")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        # Вызываем деструктор класса
        if adc is not None:
            adc.__del__()
        print("Программа завершена, ресурсы освобождены")