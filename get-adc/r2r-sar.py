import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt

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


# Основной скрипт для визуализации SAR измерений
if __name__ == "__main__":
    # 1. Импортируйте модули работы с R2R АЦП, временем и модуль для построения графика
    # (уже выполнено в начале файла)
    
    # 2. Создайте объект класса R2R_ADC
    # Задаем параметры (можно изменить)
    DYNAMIC_RANGE = 3.3  # Динамический диапазон ЦАП в Вольтах
    DURATION = 10.0      # Продолжительность измерений в секундах
    
    print("=== SAR АЦП - Визуализация напряжения ===")
    print(f"Динамический диапазон: {DYNAMIC_RANGE} В")
    print(f"Продолжительность измерений: {DURATION} с")
    print("Для досрочного завершения нажмите Ctrl+C\n")
    
    # 3. Создайте два списка:
    voltage_values = []  # Для хранения напряжений
    time_values = []     # Для хранения моментов времени от старта скрипта
    
    adc = None
    try:
        # Создаем объект класса R2R_ADC
        adc = R2R_ADC(dynamic_range=DYNAMIC_RANGE, compare_time=0.001, verbose=False)
        
        # 5. В блоке try
        # 5.1. Сохраните момент начала эксперимента
        start_time = time.time()
        measurement_count = 0
        
        print("Начало измерений...")
        print("Изменяйте напряжение потенциометра для наблюдения изменений на графике")
        
        # 5.2. Пока разница между текущим временем и начальным моментом меньше продолжительности эксперимента:
        while (time.time() - start_time) < DURATION:
            current_time = time.time() - start_time
            
            # 5.2.1. Добавляйте в список значения напряжений, измеренных методом get_sar_voltage()
            voltage = adc.get_sar_voltage()
            voltage_values.append(voltage)
            
            # 5.2.2. Добавляйте в список моменты времени
            time_values.append(current_time)
            measurement_count += 1
            
            # Выводим прогресс
            progress = (current_time / DURATION) * 100
            print(f"Прогресс: {progress:5.1f}% | Измерение {measurement_count:3d}: {current_time:5.1f} с, Напряжение: {voltage:.2f} В")
            
            # Небольшая пауза для стабильности измерений
            time.sleep(0.1)
        
        print(f"\nИзмерения завершены! Всего измерений: {measurement_count}")
        
        # 5.3. Отобразите график
        print("Построение графика...")
        plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range)
        
    except KeyboardInterrupt:
        print(f"\nИзмерения прерваны пользователем")
        if voltage_values:
            print(f"Всего выполнено измерений: {len(voltage_values)}")
            print("Построение графика по собранным данным...")
            plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range if adc else DYNAMIC_RANGE)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        # 6. В блоке finally вызовите деструктор класса
        if adc is not None:
            adc.__del__()
        print("Программа завершена, ресурсы освобождены")