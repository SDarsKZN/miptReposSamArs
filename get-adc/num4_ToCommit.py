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
        """Деструктор - выставляет 0 на выход ЦАП и очищает настройки GPIO"""
        GPIO.output(self.bits_gpio, 0)
        GPIO.cleanup()
    
    def number_to_dac(self, number):
        """Подает число number на вход ЦАП"""
        binary = format(number, '08b')
        for i, pin in enumerate(self.bits_gpio):
            GPIO.output(pin, int(binary[i]))
    
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

    def successive_approximation_adc(self):
        """Реализует алгоритм бинарного поиска напряжения на входе АЦП"""
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
        
        if self.verbose:
            print(f"Результат SAR: {result}")
        
        return result

    def get_sar_voltage(self):
        """Возвращает измеренное алгоритмом бинарного поиска напряжение в Вольтах"""
        digital_value = self.successive_approximation_adc()
        voltage = (digital_value / 255) * self.dynamic_range
        return voltage


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
    
    sampling_periods = measurement_times
    
    print(f"Всего измерений: {len(sampling_periods)}")
    print(f"Времена измерений (первые 10): {[f'{t:.3f}' for t in sampling_periods[:10]]}")
    
    plt.figure(figsize=(10, 6))
    
    # Создаем бины с периодом 0.1 секунды
    bins = np.arange(0, max(sampling_periods) + 0.1, 0.1)
    
    n, bins, patches = plt.hist(sampling_periods, bins=bins, color='lightblue', 
                               edgecolor='black', alpha=0.7, rwidth=0.8)
    
    plt.title('Распределение продолжительности измерений АЦП')
    plt.xlabel('Продолжительность измерения, с')
    plt.ylabel('Количество измерений')
    
    plt.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    # Добавляем подписи к столбцам
    for i in range(len(n)):
        if n[i] > 0:
            plt.text(bins[i] + 0.05, n[i] + 0.1, str(int(n[i])), 
                    ha='center', va='bottom', fontsize=9)
    
    mean_time = np.mean(sampling_periods)
    plt.axvline(mean_time, color='red', linestyle='--', linewidth=2, 
               label=f'Среднее: {mean_time:.3f} с')
    
    plt.text(0.02, 0.95, f'Бины: по 0.1 с', 
            transform=plt.gca().transAxes, fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    plt.text(0.02, 0.85, f'Всего измерений: {len(sampling_periods)}', 
            transform=plt.gca().transAxes, fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    plt.legend()
    
    print(f"\n=== СТАТИСТИКА ПРОДОЛЖИТЕЛЬНОСТИ ИЗМЕРЕНИЙ ===")
    print(f"Среднее время измерения: {mean_time:.3f} с")
    print(f"Минимальное время: {min(sampling_periods):.3f} с")
    print(f"Максимальное время: {max(sampling_periods):.3f} с")
    print(f"Стандартное отклонение: {np.std(sampling_periods):.3f} с")
    print(f"\nРаспределение по бинам:")
    for i in range(len(n)):
        if n[i] > 0:
            print(f"  {bins[i]:.1f}-{bins[i+1]:.1f} с: {int(n[i])} измерений")
    
    plt.tight_layout()
    plt.show()


# Основной скрипт для последовательного приближения (SAR)
if __name__ == "__main__":
    adc = None
    try:
        # Создаем объект класса R2R_ADC
        print("Инициализация АЦП...")
        adc = R2R_ADC(dynamic_range=3.3, compare_time=0.001, verbose=False)
        
        print("Начало измерений напряжения методом последовательного приближения (SAR)")
        print("Для остановки нажмите Ctrl+C\n")
        
        measurement_count = 0
        
        # Бесконечный цикл измерений
        while True:
            # Читаем напряжение методом get_sar_voltage()
            voltage = adc.get_sar_voltage()
            measurement_count += 1
            
            # Печатаем напряжение в терминал
            print(f"Измерение {measurement_count}: Напряжение = {voltage:.2f} В")
            
            # Небольшая пауза между измерениями
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\nИзмерения остановлены пользователем")
        print(f"Всего выполнено измерений: {measurement_count}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        # Вызываем деструктор объекта класса R2R_ADC
        if adc is not None:
            adc.__del__()
        print("Программа завершена, ресурсы освобождены")